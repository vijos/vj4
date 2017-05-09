from pymongo import ReturnDocument

from vj4 import db
from vj4.util import argmethod


@argmethod.wrap
async def inc_user_counter():
  """Increments the user counter.

  Returns:
    Integer value after increment.
  """
  coll = db.coll('system')
  doc = await coll.find_one_and_update(filter={'_id': 'user_counter'},
                                       update={'$inc': {'value': 1}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
  return doc['value']


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('system')
  await coll.find_one_and_update(filter={'_id': 'user_counter'},
                                 update={'$setOnInsert': {'value': 1}},
                                 upsert=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
