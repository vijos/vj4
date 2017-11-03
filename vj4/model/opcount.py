import datetime
import time

from pymongo import errors
from pymongo import ReturnDocument

from vj4 import db
from vj4 import error
from vj4.util import argmethod


@argmethod.wrap
async def inc(op: str, ident: str, period_secs: int, max_operations: int):
  coll = db.coll('opcount')
  cur_time = int(time.time())
  begin_at = datetime.datetime.utcfromtimestamp(cur_time - cur_time % period_secs)
  expire_at = begin_at + datetime.timedelta(seconds=period_secs)
  try:
    doc = await coll.find_one_and_update(filter={'ident': ident,
                                                 'begin_at': begin_at,
                                                 'expire_at': expire_at,
                                                 op: {'$not': {'$gte': max_operations}}},
                                         update={'$inc': {op: 1}},
                                         upsert=True,
                                         return_document=ReturnDocument.AFTER)
    return doc
  except errors.DuplicateKeyError:
    raise error.OpcountExceededError(op, period_secs, max_operations)


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('opcount')
  await coll.create_index([('ident', 1),
                           ('begin_at', 1),
                           ('expire_at', 1)], unique=True)
  await coll.create_index('expire_at', expireAfterSeconds=0)


if __name__ == '__main__':
  argmethod.invoke_by_args()
