import datetime

from pymongo import errors
from pymongo import ReturnDocument

from vj4 import constant
from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.model import system
from vj4.util import argmethod
from vj4.util import validator

PROJECTION_PUBLIC = {
  '_id': 1,
  'name': 1,
  'gravatar': 1
}


@argmethod.wrap
async def add(domain_id: str, owner_uid: int,
              roles=builtin.DOMAIN_SYSTEM['roles'],
              name: str=None, gravatar: str=None, bulletin: str=''):
  validator.check_domain_id(domain_id)
  validator.check_name(name)
  validator.check_bulletin(bulletin)
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.DomainAlreadyExistError(domain_id)
  coll = db.coll('domain')
  try:
    result = await coll.insert_one({'_id': domain_id,
                                    'pending': True, 'owner_uid': owner_uid,
                                    'roles': roles, 'name': name,
                                    'gravatar': gravatar, 'bulletin': bulletin})
    domain_id = result.inserted_id
  except errors.DuplicateKeyError:
    raise error.DomainAlreadyExistError(domain_id) from None
  # grant root role to owner by default
  await add_user_role(domain_id, owner_uid, builtin.ROLE_ROOT)
  await coll.update_one({'_id': domain_id},
                        {'$unset': {'pending': ''}})
  return domain_id


async def add_continue(domain_id: str, ensure_owner_uid: int=None):
  ddoc = await get(domain_id)
  if 'pending' not in ddoc:
    raise error.DomainNotFoundError(domain_id)
  owner_uid = ddoc['owner_uid']
  if ensure_owner_uid != None and owner_uid != ensure_owner_uid:
    raise error.DomainNotFoundError(domain_id)
  try:
    await add_user_role(domain_id, owner_uid, builtin.ROLE_ROOT)
  except error.UserAlreadyDomainMemberError:
    pass
  coll = db.coll('domain')
  await coll.update_one({'_id': domain_id},
                        {'$unset': {'pending': ''}})


@argmethod.wrap
async def get(domain_id: str, fields=None):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return domain
  coll = db.coll('domain')
  ddoc = await coll.find_one(domain_id, fields)
  if not ddoc:
    raise error.DomainNotFoundError(domain_id)
  return ddoc


def get_multi(*, fields=None, **kwargs):
  coll = db.coll('domain')
  return coll.find(kwargs, fields)


@argmethod.wrap
async def get_list(*, fields=None, limit: int=None, **kwargs):
  coll = db.coll('domain')
  return await coll.find(kwargs, fields).limit(limit).to_list(None)


def get_pending(**kwargs):
  return get_multi(pending=True, **kwargs)


@argmethod.wrap
async def edit(domain_id: str, **kwargs):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.BuiltinDomainError(domain_id)
  coll = db.coll('domain')
  if 'owner_uid' in kwargs:
    del kwargs['owner_uid']
  if 'name' in kwargs:
    validator.check_name(kwargs['name'])
  # TODO(twd2): check kwargs
  return await coll.find_one_and_update(filter={'_id': domain_id},
                                        update={'$set': {**kwargs}},
                                        return_document=ReturnDocument.AFTER)


async def unset(domain_id, fields):
  # TODO(twd2): check fields
  coll = db.coll('domain')
  return await coll.find_one_and_update(filter={'_id': domain_id},
                                        update={'$unset': dict((f, '') for f in set(fields))},
                                        return_document=ReturnDocument.AFTER)


@argmethod.wrap
async def inc_pid_counter(domain_id: str):
  """Increments the problem ID counter.

  Returns:
    Integer value before increment.
  """
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      return await system.inc_pid_counter()
  coll = db.coll('domain')
  await coll.update_one(filter={'_id': domain_id, 'pid_counter': {'$exists': False}},
                        update={'$set': {'pid_counter': 1000}})
  doc = await coll.find_one_and_update(filter={'_id': domain_id},
                                       update={'$inc': {'pid_counter': 1}})
  return doc['pid_counter']


@argmethod.wrap
async def set_role(domain_id: str, role: str, perm: int):
  return await set_roles(domain_id, {role: perm})


@argmethod.wrap
async def set_roles(domain_id: str, roles):
  roles = {str(role): int(perm) for role, perm in roles.items()}
  update = {}
  for role in roles:
    validator.check_role(role)
    if role in builtin.BUILTIN_ROLE_DESCRIPTORS:
      if not builtin.BUILTIN_ROLE_DESCRIPTORS[role].modifiable:
        raise error.ModifyBuiltinRoleError(domain_id, role)
    update['roles.{0}'.format(role)] = roles[role]
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.BuiltinDomainError(domain_id)
  coll = db.coll('domain')
  return await coll.find_one_and_update(filter={'_id': domain_id},
                                        update={'$set': update},
                                        return_document=ReturnDocument.AFTER)


@argmethod.wrap
async def delete_role(domain_id: str, role: str):
  return await delete_roles(domain_id, [role])


async def delete_roles(domain_id: str, roles):
  roles = list(set(roles))
  for role in roles:
    validator.check_role(role)
    if role in builtin.BUILTIN_ROLE_DESCRIPTORS:
      raise error.ModifyBuiltinRoleError(domain_id, role)
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.BuiltinDomainError(domain_id)
  user_coll = db.coll('domain.user')
  await user_coll.update_many({'domain_id': domain_id, 'role': {'$in': list(roles)}},
                              {'$unset': {'role': ''}})
  coll = db.coll('domain')
  return await coll.find_one_and_update(filter={'_id': domain_id},
                                        update={'$unset': dict(('roles.{0}'.format(role), '')
                                                               for role in roles)},
                                        return_document=ReturnDocument.AFTER)


@argmethod.wrap
async def transfer(domain_id: str, old_owner_uid: int, new_owner_uid: int):
  for domain in builtin.DOMAINS:
    if domain['_id'] == domain_id:
      raise error.BuiltinDomainError(domain_id)
  coll = db.coll('domain')
  return await coll.find_one_and_update(filter={'_id': domain_id, 'owner_uid': old_owner_uid},
                                        update={'$set': {'owner_uid': new_owner_uid}},
                                        return_document=ReturnDocument.AFTER)


@argmethod.wrap
async def get_user(domain_id: str, uid: int, fields=None):
  coll = db.coll('domain.user')
  return await coll.find_one({'domain_id': domain_id, 'uid': uid}, fields)


async def set_user(domain_id, uid, **kwargs):
  coll = db.coll('domain.user')
  return await coll.find_one_and_update(filter={'domain_id': domain_id, 'uid': uid},
                                        update={'$set': kwargs},
                                        upsert=True,
                                        return_document=ReturnDocument.AFTER)


async def unset_user(domain_id, uid, fields):
  coll = db.coll('domain.user')
  return await coll.find_one_and_update(filter={'domain_id': domain_id, 'uid': uid},
                                        update={'$unset': dict((f, '') for f in set(fields))},
                                        upsert=True,
                                        return_document=ReturnDocument.AFTER)


async def set_users(domain_id, uids, **kwargs):
  coll = db.coll('domain.user')
  await coll.update_many({'domain_id': domain_id, 'uid': {'$in': list(set(uids))}},
                         {'$set': kwargs},
                         upsert=False)


async def unset_users(domain_id, uids, fields):
  coll = db.coll('domain.user')
  await coll.update_many({'domain_id': domain_id, 'uid': {'$in': list(set(uids))}},
                         {'$unset': dict((f, '') for f in set(fields))},
                         upsert=True)


@argmethod.wrap
async def add_user_role(domain_id: str, uid: int, role: str, join_at=None):
  validator.check_role(role)
  if join_at is None:
    join_at = datetime.datetime.utcnow()
  coll = db.coll('domain.user')
  try:
    await coll.update_one({'domain_id': domain_id, 'uid': uid,
                           'role': {'$exists': False}},
                           {'$set': {'role': role, 'join_at': join_at}},
                           upsert=True)
  except errors.DuplicateKeyError:
    raise error.UserAlreadyDomainMemberError(domain_id, uid) from None
  return True


@argmethod.wrap
async def set_user_role(domain_id: str, uid: int, role: str):
  validator.check_role(role)
  # use set_users to utilize "upsert=False"
  return await set_users(domain_id, [uid], role=role)


@argmethod.wrap
async def unset_user_role(domain_id: str, uid: int):
  return await unset_user(domain_id, uid, ['role'])


async def set_users_role(domain_id: str, uids, role: str):
  validator.check_role(role)
  await set_users(domain_id, uids, role=role)


async def unset_users_role(domain_id: str, uids):
  await unset_users(domain_id, uids, ['role'])


async def inc_user(domain_id, uid, **kwargs):
  coll = db.coll('domain.user')
  return await coll.find_one_and_update(filter={'domain_id': domain_id, 'uid': uid},
                                        update={'$inc': kwargs},
                                        upsert=True,
                                        return_document=ReturnDocument.AFTER)


async def inc_user_usage(domain_id: str, uid: int, usage_field: str, usage: int, quota: int):
  coll = db.coll('domain.user')
  try:
    return await coll.find_one_and_update(filter={'domain_id': domain_id, 'uid': uid,
                                                  usage_field: {'$not': {'$gte': quota - usage}}},
                                          update={'$inc': {usage_field: usage}},
                                          upsert=True,
                                          return_document=ReturnDocument.AFTER)
  except errors.DuplicateKeyError:
    raise error.UsageExceededError(domain_id, uid, usage_field, usage, quota)


def get_multi_user(*, fields=None, **kwargs):
  coll = db.coll('domain.user')
  return coll.find(kwargs, fields)


async def get_dict_user_by_uid(domain_id, uids, *, fields=None):
  result = dict()
  async for dudoc in get_multi_user(
      domain_id=domain_id, uid={'$in': list(set(uids))}, fields=fields):
    result[dudoc['uid']] = dudoc
  return result


async def get_dict_user_by_domain_id(uid, *, fields=None):
  result = dict()
  async for dudoc in get_multi_user(uid=uid, fields=fields):
    result[dudoc['domain_id']] = dudoc
  return result


def get_all_roles(ddoc):
  builtin_roles = {role: rd.default_permission for role, rd in builtin.BUILTIN_ROLE_DESCRIPTORS.items()}
  domain_roles = ddoc['roles']
  return {**builtin_roles, **domain_roles}


def get_join_settings(ddoc, now):
  if 'join' not in ddoc:
    return None
  join_settings = ddoc['join']
  if not join_settings:
    return None
  if join_settings['method'] == constant.domain.JOIN_METHOD_NONE:
    return None
  if join_settings['role'] not in ddoc['roles']:
    return None
  if join_settings['expire'] != None and join_settings['expire'] < now:
    return None
  return join_settings


@argmethod.wrap
async def get_prefix_search(prefix: str, fields={}, limit: int=50):
  builtin_ddocs = []
  for domain in builtin.DOMAINS:
    if domain['_id'][:len(prefix)] == prefix or domain['name'][:len(prefix)] == prefix:
      builtin_ddocs.append(domain)
  regex = r'\A\Q{0}\E'.format(prefix.replace(r'\E', r'\E\\E\Q'))
  coll = db.coll('domain')
  ddocs = await coll.find({'$or': [{'_id': {'$regex': regex}},
                                   {'name': {'$regex': regex}}]},
                          projection=fields) \
                    .limit(limit) \
                    .to_list()
  return builtin_ddocs + ddocs


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('domain')
  await coll.create_index('owner_uid')
  await coll.create_index('name')
  user_coll = db.coll('domain.user')
  await user_coll.create_index('uid')
  await user_coll.create_index([('domain_id', 1),
                                ('uid', 1)], unique=True)
  await user_coll.create_index([('domain_id', 1),
                                ('role', 1)], sparse=True)
  await user_coll.create_index([('domain_id', 1),
                                ('rp', -1)])
  await user_coll.create_index([('domain_id', 1),
                                ('rank', 1)])


if __name__ == '__main__':
  argmethod.invoke_by_args()
