from bson import objectid

from vj4 import db
from vj4.util import argmethod

TYPE_DELETE_DOCUMENT = 1
TYPE_DELETE_SUB_DOCUMENT = 2
TYPE_REJUDGE = 3 # TODO(twd2)


@argmethod.wrap
async def add(uid: int, type: int, **kwargs):
  """Add an operation log. Returns the document id."""
  obj_id = objectid.ObjectId()
  coll = db.coll('oplog')
  doc = {'_id': obj_id,
         'uid': uid,
         'type': type,
         **kwargs}
  await coll.insert_one(doc)
  return obj_id


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('oplog')
  await coll.create_index('uid')
  # type delete document
  await coll.create_index([('doc.domain_id', 1),
                           ('doc.doc_type', 1),
                           ('doc.doc_id', 1)], sparse=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
