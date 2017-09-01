import asyncio
import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import domain
from vj4.model import document
from vj4.model import fs
from vj4.model.adaptor import userfile
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


@argmethod.wrap
async def sync_length():
  _logger.info('Userfile length')
  coll = db.coll('document')
  ufdocs = userfile.get_multi()
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Syncing')
  async for ufdoc in ufdocs:
    l = 0
    if ufdoc.get('file_id'):
      fdoc = await fs.get_meta(ufdoc['file_id'])
      if fdoc and fdoc.get('length'):
        l = fdoc['length']
    bulk.find({'_id': ufdoc['_id']}) \
        .update_one({'$set': {'length': l}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()


@argmethod.wrap
async def sync_usage():
  _logger.info('Userfile length group by user')
  pipeline = [
    {
      '$match': {'domain_id': userfile.STORE_DOMAIN_ID,
                 'doc_type': document.TYPE_USERFILE}
    },
    {
      '$group': {
        '_id': '$owner_uid',
        'usage_userfile': {'$sum': '$length'}
      }
    }
  ]
  coll = db.coll('domain.user')
  await coll.update_many({'domain_id': userfile.STORE_DOMAIN_ID},
                         {'$set': {'usage_userfile': 0}})
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document').aggregate(pipeline):
    bulk.find({'domain_id': userfile.STORE_DOMAIN_ID,
               'uid': adoc['_id']}) \
        .update_one({'$set': {'usage_userfile': adoc['usage_userfile']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()


@argmethod.wrap
async def sync():
  await sync_length()
  await sync_usage()


if __name__ == '__main__':
  argmethod.invoke_by_args()
