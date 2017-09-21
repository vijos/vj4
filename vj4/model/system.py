import random

from pymongo import errors
from pymongo import ReturnDocument

from vj4 import db
from vj4 import error
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
  await coll.update_one(filter={'_id': 'user_counter'},
                        update={'$setOnInsert': {'value': 1}},
                        upsert=True)


async def acquire_lock(lock_name: str):
  lock_value = random.randint(1, 0xFFFFFFFF)
  coll = db.coll('system')
  try:
    await coll.update_one(filter={'_id': 'lock_' + lock_name, 'value': 0},
                          update={'$set': {'value': lock_value}},
                          upsert=True)
  except errors.DuplicateKeyError:
    return None
  return lock_value


async def release_lock(lock_name: str, lock_value: int):
  coll = db.coll('system')
  result = await coll.update_one(filter={'_id': 'lock_' + lock_name, 'value': lock_value},
                                 update={'$set': {'value': 0}})
  if result.matched_count == 0:
    return None
  return True


async def release_lock_anyway(lock_name: str):
  coll = db.coll('system')
  await coll.update_one(filter={'_id': 'lock_' + lock_name},
                        update={'$set': {'value': 0}})
  return True


async def acquire_upgrade_lock():
  lock = await acquire_lock('upgrade')
  if not lock:
    raise error.UpgradeLockAcquireError()
  return lock


async def release_upgrade_lock(lock: int):
  success = await release_lock('upgrade', lock)
  if not success:
    raise error.UpgradeLockReleaseError()
  return True


@argmethod.wrap
async def release_upgrade_lock_anyway():
  return await release_lock_anyway('upgrade')


@argmethod.wrap
async def get_db_version():
  coll = db.coll('system')
  doc = await coll.find_one({'_id': 'db_version'})
  if doc is None:
    return 0
  else:
    return doc['value']


async def set_db_version(version: int):
  coll = db.coll('system')
  result = await coll.update_one(filter={'_id': 'db_version'},
                        update={'$set': {'value': version}})
  return result.modified_count


async def ensure_db_version(allowed_version):
  current_version = await get_db_version()
  if current_version != allowed_version:
    raise error.DatabaseVersionMismatchError(current_version, allowed_version)


if __name__ == '__main__':
  argmethod.invoke_by_args()
