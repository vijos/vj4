import datetime
from vj4 import db
from vj4.util import argmethod


@argmethod.wrap
async def add(ip: str):
  coll = db.coll('blacklist')
  expire_at = datetime.datetime.utcnow() + datetime.timedelta(days=365)
  await coll.find_one_and_update({'_id': ip},
                                 {'$set': {'expire_at': expire_at}},
                                 upsert=True)


@argmethod.wrap
async def get(ip: str):
  coll = db.coll('blacklist')
  return await coll.find_one({'_id': ip})


@argmethod.wrap
async def delete(ip: str):
  coll = db.coll('blacklist')
  await coll.delete_one({'_id': ip})


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('blacklist')
  await coll.create_index('expire_at', expireAfterSeconds=0)


if __name__ == '__main__':
  argmethod.invoke_by_args()
