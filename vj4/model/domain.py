from pymongo import errors

from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.util import argmethod


@argmethod.wrap
async def add(domain_id: str, owner_uid: int,
              roles={builtin.ROLE_DEFAULT: builtin.DEFAULT_PERMISSIONS}):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.DomainAlreadyExistError(domain_id)
  coll = db.Collection('domain')
  # TODO(twd2): Do we need to check owner's priv, quota, etc here?
  try:
    return await coll.insert({'_id': domain_id, 'owner_uid': owner_uid, 'roles': roles})
  except errors.DuplicateKeyError:
    raise error.DomainAlreadyExistError(domain_id) from None


@argmethod.wrap
async def get(domain_id: str):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return domain
  coll = db.Collection('domain')
  return await coll.find_one(domain_id)


def get_multi():
  coll = db.Collection('domain')
  return coll.find()


@argmethod.wrap
async def transfer(domain_id: str, old_owner_uid: int, new_owner_uid: int):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return None
  coll = db.Collection('domain')
  # TODO(twd2): Do we need to check new owner's priv, quota, etc here?
  return await coll.find_and_modify(query={'_id': domain_id, 'owner_uid': old_owner_uid},
                                    update={'$set': {'owner_uid': new_owner_uid}},
                                    new=True)


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('domain')
  await coll.ensure_index('owner_uid')


if __name__ == '__main__':
  argmethod.invoke_by_args()
