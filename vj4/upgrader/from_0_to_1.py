import datetime
import logging

from vj4 import db
from vj4.model import builtin
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

    ddocs = await domain.get_multi().to_list()
    for ddoc in ddocs:
      _logger.info('Updating domain {0}...'.format(ddoc['_id']))
      owner_uid = ddoc['owner_uid']
      # assign `root` role to owner
      await domain.set_user(ddoc['_id'], owner_uid, role=builtin.ROLE_ROOT)

    # add `join_at` attribute
    _logger.info('Updating join_at ...')
    coll_domain_user = db.coll('domain.user')
    await coll_domain_user.update_many({'role': {'$exists': True}, 'join_at': {'$exists': False}},
                                       {'$set': {'join_at': datetime.datetime.utcfromtimestamp(0)}})

    _logger.info('Bumping database version...')
    await system.set_db_version(1)
  finally:
    await system.release_upgrade_lock(lock)


if __name__ == '__main__':
  argmethod.invoke_by_args()
