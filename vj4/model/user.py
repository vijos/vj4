import datetime

from pymongo import errors

from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.util import argmethod
from vj4.util import pwhash
from vj4.util import validator


PROJECTION_PUBLIC = {'_id': 1,
                     'uname': 1,
                     'uname_lower': 1,
                     'mail': 1,
                     'mail_lower': 1,
                     'gravatar': 1}
PROJECTION_VIEW = {'salt': 0, 'hash': 0}
PROJECTION_ALL = None


@argmethod.wrap
async def add(uid: int, uname: str, password: str, mail: str, regip: str = ''):
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
  coll = db.Collection('user')
  try:
    await coll.insert({'_id': uid,
                       'uname': uname,
                       'uname_lower': uname_lower,
                       'mail': mail,
                       'mail_lower': mail_lower,
                       'salt': salt,
                       'hash': pwhash.hash_vj4(password, salt),
                       'regat': datetime.datetime.utcnow(),
                       'regip': regip,
                       'roles': {},
                       'priv': builtin.PRIV_USER_PROFILE,
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
  coll = db.Collection('user')
  return await coll.find_one({'_id': uid}, fields)


@argmethod.wrap
async def get_by_uname(uname: str, fields=PROJECTION_VIEW):
  """Get a user by uname."""
  uname_lower = uname.strip().lower()
  for user in builtin.USERS:
    if user['uname_lower'] == uname_lower:
      return user
  coll = db.Collection('user')
  return await coll.find_one({'uname_lower': uname_lower}, fields)


@argmethod.wrap
async def get_by_mail(mail: str, fields=PROJECTION_VIEW):
  """Get a user by mail."""
  mail_lower = mail.strip().lower()
  for user in builtin.USERS:
    if user['mail_lower'] == mail_lower:
      return user
  coll = db.Collection('user')
  return await coll.find_one({'mail_lower': mail_lower}, fields)


@argmethod.wrap
async def check_password_by_uid(uid: int, password: str):
  """Check password. Returns doc or None."""
  doc = await get_by_uid(uid, PROJECTION_ALL)
  if doc and pwhash.check(password, doc['salt'], doc['hash']):
    return doc


@argmethod.wrap
async def check_password_by_uname(uname: str, password: str):
  """Check password. Returns doc or None."""
  doc = await get_by_uname(uname, PROJECTION_ALL)
  if doc and pwhash.check(password, doc['salt'], doc['hash']):
    return doc


@argmethod.wrap
async def set_password(uid: int, password: str):
  """Set password. Returns doc or None."""
  validator.check_password(password)
  salt = pwhash.gen_salt()
  coll = db.Collection('user')
  doc = await coll.find_and_modify(query={'_id': uid},
                                   update={'$set': {'salt': salt,
                                                    'hash': pwhash.hash_vj4(password, salt)}},
                                   new=True)
  return doc


@argmethod.wrap
async def set_mail(uid: int, mail: str):
  """Set password. Returns doc or None."""
  return await set_by_uid(uid, mail=mail, mail_lower=mail.strip().lower())


@argmethod.wrap
async def change_password(uid: int, current_password: str, password: str):
  """Change password. Returns doc or None."""
  doc = await check_password_by_uid(uid, current_password)
  if not doc:
    return None
  validator.check_password(password)
  salt = pwhash.gen_salt()
  coll = db.Collection('user')
  doc = await coll.find_and_modify(query={'_id': doc['_id'],
                                          'salt': doc['salt'],
                                          'hash': doc['hash']},
                                   update={'$set': {'salt': salt,
                                                    'hash': pwhash.hash_vj4(password, salt)}},
                                   new=True)
  return doc


async def set_by_uid(uid, **kwargs):
  coll = db.Collection('user')
  doc = await coll.find_and_modify(query={'_id': uid}, update={'$set': kwargs}, new=True)
  return doc


async def attach_udocs(docs, field_name, udoc_field_name='udoc', fields=PROJECTION_VIEW):
  """Attach udoc to docs by uid in the specified field."""
  # TODO(iceboy): projection.
  uids = set(doc[field_name] for doc in docs)
  if uids:
    coll = db.Collection('user')
    udocs = await coll.find({'_id': {'$in': list(uids)}}, fields).to_list(None)
    uids = dict((udoc['_id'], udoc) for udoc in udocs)
    uids.update(dict((udoc['_id'], udoc) for udoc in builtin.USERS))
    for doc in docs:
      doc[udoc_field_name] = uids.get(doc[field_name])
  return docs


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('user')
  await coll.ensure_index('uname_lower', unique=True)
  await coll.ensure_index('mail_lower', sparse=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
