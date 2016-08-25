from pymongo import errors

from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.util import argmethod
from vj4.util import validator


PROJECTION_PUBLIC = {'uid': 1}


@argmethod.wrap
async def add(domain_id: str, owner_uid: int,
              roles=builtin.DOMAIN_SYSTEM['roles'],
              description: str=None):
  validator.check_domain_id(domain_id)
  if description != None:
    validator.check_description(description)
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.DomainAlreadyExistError(domain_id)
  coll = db.Collection('domain')
  try:
    return await coll.insert({'_id': domain_id, 'owner_uid': owner_uid,
                              'description': description, 'roles': roles})
  except errors.DuplicateKeyError:
    raise error.DomainAlreadyExistError(domain_id) from None


@argmethod.wrap
async def get(domain_id: str, fields=None):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return domain
  coll = db.Collection('domain')
  return await coll.find_one(domain_id, fields)


def get_multi(owner_uid=None, fields=None):
  coll = db.Collection('domain')
  query = {}
  if owner_uid != None:
    query['owner_uid'] = owner_uid
  return coll.find(query, fields)


@argmethod.wrap
async def get_list(owner_uid: int=None, fields=None, limit: int=None):
  coll = db.Collection('domain')
  query = {}
  if owner_uid != None:
    query['owner_uid'] = owner_uid
  return await coll.find(query, fields).to_list(None)


@argmethod.wrap
async def edit(domain_id: str, **kwargs):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return None
  coll = db.Collection('domain')
  if 'owner_uid' in kwargs:
    del kwargs['owner_uid']
  if 'description' in kwargs and kwargs['description'] != None:
    validator.check_description(kwargs['description'])
  # TODO(twd2): check kwargs
  return await coll.find_and_modify(query={'_id': domain_id},
                                    update={'$set': {**kwargs}},
                                    new=True)


async def unset(domain_id, fields):
  # TODO(twd2): check fields
  coll = db.Collection('domain')
  return await coll.find_and_modify(query={'_id': domain_id},
                                    update={'$unset': dict((f, '') for f in set(fields))},
                                    new=True)


@argmethod.wrap
async def set_role(domain_id: str, role: str, perm: int):
  validator.check_role(role)
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return domain
  coll = db.Collection('domain')
  return await coll.find_and_modify(query={'_id': domain_id},
                                    update={'$set': {'roles.{0}'.format(role): perm}},
                                    new=True)


@argmethod.wrap
async def delete_role(domain_id: str, role: str):
  validator.check_role(role)
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return domain
  user_coll = db.Collection('domain.user')
  await user_coll.update({'domain_id': domain_id, 'role': role},
                         {'$unset': {'role': ''}}, multi=True)
  coll = db.Collection('domain')
  return await coll.find_and_modify(query={'_id': domain_id},
                                    update={'$unset': {'roles.{0}'.format(role): ''}},
                                    new=True)


@argmethod.wrap
async def transfer(domain_id: str, old_owner_uid: int, new_owner_uid: int):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return None
  coll = db.Collection('domain')
  return await coll.find_and_modify(query={'_id': domain_id, 'owner_uid': old_owner_uid},
                                    update={'$set': {'owner_uid': new_owner_uid}},
                                    new=True)


@argmethod.wrap
async def get_user(domain_id: str, uid: int, fields=None):
  coll = db.Collection('domain.user')
  return await coll.find_one({'domain_id': domain_id, 'uid': uid}, fields)


async def set_user(domain_id, uid, **kwargs):
  coll = db.Collection('domain.user')
  return await coll.find_and_modify(query={'domain_id': domain_id, 'uid': uid},
                                    update={'$set': kwargs},
                                    upsert=True,
                                    new=True)


async def unset_user(domain_id, uid, fields):
  coll = db.Collection('domain.user')
  return await coll.find_and_modify(query={'domain_id': domain_id, 'uid': uid},
                                    update={'$unset': dict((f, '') for f in set(fields))},
                                    upsert=True,
                                    new=True)


@argmethod.wrap
async def set_user_role(domain_id: str, uid: int, role: str):
  validator.check_role(role)
  return await set_user(domain_id, uid, role=role)


@argmethod.wrap
async def unset_user_role(domain_id: str, uid: int):
  return await unset_user(domain_id, uid, ['role'])


async def inc_user(domain_id, uid, **kwargs):
  coll = db.Collection('domain.user')
  return await coll.find_and_modify(query={'domain_id': domain_id, 'uid': uid},
                                    update={'$inc': kwargs},
                                    upsert=True,
                                    new=True)


@argmethod.wrap
def get_multi_user(domain_id: str, *, fields=None, **kwargs):
  coll = db.Collection('domain.user')
  return coll.find({'domain_id': domain_id, **kwargs}, fields)


async def get_dict_user(domain_id, uids, *, fields=None):
  result = dict()
  async for dudoc in get_multi_user(domain_id, uid={'$in': list(set(uids))}, fields=fields):
    result[dudoc['uid']] = dudoc
  return result


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('domain')
  await coll.ensure_index('owner_uid')
  user_coll = db.Collection('domain.user')
  await user_coll.ensure_index([('domain_id', 1),
                                ('uid', 1)], unique=True)
  await user_coll.ensure_index([('domain_id', 1),
                                ('role', 1)], sparse=True)
  await user_coll.ensure_index([('domain_id', 1),
                                ('rp', -1)])
  await user_coll.ensure_index([('domain_id', 1),
                                ('rank', 1)])


if __name__ == '__main__':
  argmethod.invoke_by_args()
