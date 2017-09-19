import logging

from vj4 import db
from vj4.model import domain
from vj4.model import system
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


@argmethod.wrap
async def run():
  lock = await system.acquire_upgrade_lock()
  try:
    await system.ensure_db_version(0)
    coll_domain = db.coll('domain')
    await coll_domain.drop_index([('owner_uid', 1)])
    ddocs = await domain.get_multi().to_list()
    for ddoc in ddocs:
      _logger.info('Updating domain {0}...'.format(ddoc['_id']))
      owner_uid = ddoc['owner_uid']
      # add or override owner role
      await coll_domain.update_one({'_id': ddoc['_id']},
                                   {'$set': {'roles.owner': -1}, '$unset': {'owner_uid': ''}})
      # add owner_uid to owner
      await domain.set_user(ddoc['_id'], owner_uid, role='owner')
    _logger.info('Bumping database version...')
    await system.set_db_version(20170919)
  finally:
    await system.release_upgrade_lock(lock)


if __name__ == '__main__':
  argmethod.invoke_by_args()
