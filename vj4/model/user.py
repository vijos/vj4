import datetime

from pymongo import errors
from pymongo import ReturnDocument

from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.util import argmethod
from vj4.util import pwhash
from vj4.util import validator

PROJECTION_PUBLIC = {'_id': 1,
                     'uname': 1,
                     'uname_lower': 1,
                     'gravatar': 1}
PROJECTION_VIEW = {'salt': 0, 'hash': 0}
PROJECTION_ALL = None


@argmethod.wrap
async def add(uid: int, uname: str, password: str, mail: str, regip: str=''):
  """Add a user."""
  validator.check_uname(uname)
  # TODO(iceboy): Filter uname by keywords.
  validator.check_password(password)
  validator.check_mail(mail)

  uname_lower = uname.strip().lower()
  mail_lower = mail.strip().lower()

  for user in builtin.USERS:
    if user['_id'] == uid or user['uname_lower'] == uname_lower or user['mail_lower'] == mail_lower:
      raise error.UserAlreadyExistError(uname)

  salt = pwhash.gen_salt()
  coll = db.coll('user')
  try:
    await coll.insert_one({'_id': uid,
                           'uname': uname,
                           'uname_lower': uname_lower,
                           'mail': mail,
                           'mail_lower': mail_lower,
                           'salt': salt,
                           'hash': pwhash.hash_vj4(password, salt),
                           'regat': datetime.datetime.utcnow(),
                           'regip': regip,
                           'priv': builtin.DEFAULT_PRIV,
                           'loginat': datetime.datetime.utcnow(),
                           'loginip': regip,
                           'gravatar': mail})
  except errors.DuplicateKeyError:
    raise error.UserAlreadyExistError(uid, uname, mail) from None


@argmethod.wrap
async def get_by_uid(uid: int, fields=PROJECTION_VIEW):
  """Get a user by uid."""
  for user in builtin.USERS:
    if user['_id'] == uid:
      return user
  coll = db.coll('user')
  return await coll.find_one({'_id': uid}, fields)


@argmethod.wrap
async def get_by_uname(uname: str, fields=PROJECTION_VIEW):
  """Get a user by uname."""
  uname_lower = uname.strip().lower()
  for user in builtin.USERS:
    if user['uname_lower'] == uname_lower:
      return user
  coll = db.coll('user')
  return await coll.find_one({'uname_lower': uname_lower}, fields)


@argmethod.wrap
async def get_by_mail(mail: str, fields=PROJECTION_VIEW):
  """Get a user by mail."""
  mail_lower = mail.strip().lower()
  for user in builtin.USERS:
    if user['mail_lower'] == mail_lower:
      return user
  coll = db.coll('user')
  return await coll.find_one({'mail_lower': mail_lower}, fields)


def get_multi(*, fields=PROJECTION_VIEW, **kwargs):
  """Get multiple users."""
  coll = db.coll('user')
  return coll.find(kwargs, fields)


async def get_dict(uids, *, fields=PROJECTION_VIEW):
  uid_set = set(uids)
  result = dict()
  for doc in builtin.USERS:
    if doc['_id'] in uid_set:
      result[doc['_id']] = doc
      uid_set.remove(doc['_id'])
  async for doc in get_multi(_id={'$in': list(uid_set)}, fields=fields):
    result[doc['_id']] = doc
  return result


@argmethod.wrap
async def check_password_by_uid(uid: int, password: str):
  """Check password. Returns doc or None."""
  doc = await get_by_uid(uid, PROJECTION_ALL)
  if doc and pwhash.check(password, doc['salt'], doc['hash']):
    return doc


@argmethod.wrap
async def check_password_by_uname(uname: str, password: str, auto_upgrade: bool=False):
  """Check password. Returns doc or None."""
  doc = await get_by_uname(uname, PROJECTION_ALL)
  if not doc:
    raise error.UserNotFoundError(uname)
  if pwhash.check(password, doc['salt'], doc['hash']):
    if auto_upgrade and pwhash.need_upgrade(doc['hash']) \
        and validator.is_password(password):
      await set_password(doc['_id'], password)
    return doc


@argmethod.wrap
async def set_password(uid: int, password: str):
  """Set password. Returns doc or None."""
  validator.check_password(password)
  salt = pwhash.gen_salt()
  coll = db.coll('user')
  doc = await coll.find_one_and_update(filter={'_id': uid},
                                       update={'$set': {'salt': salt,
                                                        'hash': pwhash.hash_vj4(password, salt)}},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def set_mail(uid: int, mail: str):
  """Set mail. Returns doc or None."""
  validator.check_mail(mail)
  return await set_by_uid(uid, mail=mail, mail_lower=mail.strip().lower())


@argmethod.wrap
async def change_password(uid: int, current_password: str, password: str):
  """Change password. Returns doc or None."""
  doc = await check_password_by_uid(uid, current_password)
  if not doc:
    return None
  validator.check_password(password)
  salt = pwhash.gen_salt()
  coll = db.coll('user')
  doc = await coll.find_one_and_update(filter={'_id': doc['_id'],
                                               'salt': doc['salt'],
                                               'hash': doc['hash']},
                                       update={'$set': {'salt': salt,
                                                        'hash': pwhash.hash_vj4(password, salt)}},
                                       return_document=ReturnDocument.AFTER)
  return doc


async def set_by_uid(uid, **kwargs):
  coll = db.coll('user')
  doc = await coll.find_one_and_update(filter={'_id': uid}, update={'$set': kwargs}, return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def set_priv(uid: int, priv: int):
  """Set privilege. Returns doc or None."""
  return await set_by_uid(uid, priv=priv)


@argmethod.wrap
async def set_superadmin(uid: int):
  return await set_priv(uid, builtin.PRIV_ALL)


set_superadmin = None


@argmethod.wrap
async def set_judge(uid: int):
  return await set_priv(uid, builtin.JUDGE_PRIV)


@argmethod.wrap
async def set_default(uid: int):
  return await set_priv(uid, builtin.DEFAULT_PRIV)


@argmethod.wrap
async def get_prefix_list(prefix: str, fields=PROJECTION_VIEW, limit: int=50):
  prefix = prefix.lower()
  regex = '\\A\\Q{0}\\E'.format(prefix.replace('\\E', '\\E\\\\E\\Q'))
  coll = db.coll('user')
  udocs = await coll.find({'uname_lower': {'$regex': regex}}, projection=fields) \
                    .limit(limit) \
                    .to_list()
  for udoc in builtin.USERS:
    if udoc['uname_lower'].startswith(prefix):
      udocs.append(udoc)
  return udocs


@argmethod.wrap
async def count(**kwargs):
  coll = db.coll('user')
  return coll.find({**kwargs}).count()


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('user')
  await coll.create_index('uname_lower', unique=True)
  await coll.create_index('mail_lower', sparse=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
