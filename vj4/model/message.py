import datetime

from bson import objectid

from vj4 import db
from vj4.util import argmethod
from vj4.util import validator

STATUS_READ = 1


@argmethod.wrap
async def add(sender_uid: int, sendee_uid: int, content: str):
  """Send a message from sender to sendee with specified content."""
  validator.check_content(content)
  coll = db.Collection('message')
  mdoc = {'sender_uid': sender_uid,
          'sendee_uid': sendee_uid,
          'status': 0,
          'reply': [{'sender_uid': sender_uid,
                     'content': content,
                     'status': 0,
                     'at': datetime.datetime.utcnow()}]}
  await coll.insert(mdoc)
  return mdoc


@argmethod.wrap
def get_multi(uid: int, *, fields=None):
  """Get messages related to a specified user."""
  coll = db.Collection('message')
  return coll.find({'$or': [{'sender_uid': uid}, {'sendee_uid': uid}]}, fields=fields)


@argmethod.wrap
async def add_reply(message_id: objectid.ObjectId, sender_uid: int, content: str):
  """Reply a message with specified content."""
  validator.check_content(content)
  coll = db.Collection('message')
  reply = {'sender_uid': sender_uid,
           'content': content,
           'status': 0,
           'at': datetime.datetime.utcnow()}
  mdoc = await coll.find_and_modify(query={'_id': message_id},
                                    update={'$push': {'reply': reply}},
                                    new=True)
  return (mdoc, reply)


@argmethod.wrap
async def delete(message_id: objectid.ObjectId, uid: int = None):
  """Delete a message."""
  coll = db.Collection('message')
  query = {'_id': message_id}
  if uid:
    query['$or'] = [{'sender_uid': uid}, {'sendee_uid': uid}]
  doc = await coll.remove(query)
  return bool(doc['n'])


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('user.message')
  await coll.ensure_index([('sender_uid', 1), ('_id', -1)])
  await coll.ensure_index([('sendee_uid', 1), ('_id', -1)])


if __name__ == '__main__':
  argmethod.invoke_by_args()
