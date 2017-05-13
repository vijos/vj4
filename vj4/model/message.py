import datetime

from bson import objectid
from pymongo import ReturnDocument

from vj4 import db
from vj4.util import argmethod
from vj4.util import validator

STATUS_UNREAD = 0
STATUS_READ = 1


@argmethod.wrap
async def add(sender_uid: int, sendee_uid: int, content: str):
  """Send a message from sender to sendee with specified content."""
  validator.check_content(content)
  coll = db.coll('message')
  mdoc = {'sender_uid': sender_uid,
          'sendee_uid': sendee_uid,
          'status': STATUS_UNREAD,
          'reply': [{'sender_uid': sender_uid,
                     'content': content,
                     'status': STATUS_UNREAD,
                     'at': datetime.datetime.utcnow()}]}
  await coll.insert_one(mdoc)
  return mdoc


@argmethod.wrap
def get_multi(uid: int, *, fields=None):
  """Get messages related to a specified user."""
  coll = db.coll('message')
  return coll.find({'$or': [{'sender_uid': uid}, {'sendee_uid': uid}]}, projection=fields)


@argmethod.wrap
async def add_reply(message_id: objectid.ObjectId, sender_uid: int, content: str):
  """Reply a message with specified content."""
  validator.check_content(content)
  coll = db.coll('message')
  reply = {'sender_uid': sender_uid,
           'content': content,
           'status': STATUS_UNREAD,
           'at': datetime.datetime.utcnow()}
  mdoc = await coll.find_one_and_update(filter={'_id': message_id},
                                        update={'$push': {'reply': reply}},
                                        return_document=ReturnDocument.AFTER)
  return (mdoc, reply)


@argmethod.wrap
async def delete(message_id: objectid.ObjectId, uid: int=None):
  """Delete a message."""
  coll = db.coll('message')
  query = {'_id': message_id}
  if uid:
    query['$or'] = [{'sender_uid': uid}, {'sendee_uid': uid}]
  result = await coll.delete_one(query)
  return bool(result.deleted_count)


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('message')
  await coll.create_index([('sender_uid', 1), ('_id', -1)])
  await coll.create_index([('sendee_uid', 1), ('_id', -1)])


if __name__ == '__main__':
  argmethod.invoke_by_args()
