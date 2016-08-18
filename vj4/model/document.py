import datetime

from bson import objectid

from vj4 import db
from vj4.util import argmethod

TYPE_PROBLEM = 10
TYPE_PROBLEM_SOLUTION = 11
TYPE_PROBLEM_LIST = 12
TYPE_DISCUSSION_NODE = 20
TYPE_DISCUSSION = 21
TYPE_DISCUSSION_REPLY = 22
TYPE_CONTEST = 30
TYPE_TRAINING = 40
TYPE_PRETEST_DATA = 50

DOC_ID_DISCUSSION_NODES = 1


def convert_doc_id(doc_id):
  if doc_id is None:
    return None
  if objectid.ObjectId.is_valid(doc_id):
    return objectid.ObjectId(doc_id)
  try:
    return int(doc_id)
  except ValueError:
    return str(doc_id)


@argmethod.wrap
async def add(domain_id: str, content: str, owner_uid: int,
              doc_type: int, doc_id: convert_doc_id = None,
              parent_doc_type: int = None, parent_doc_id: convert_doc_id = None, **kwargs):
  """Add a document. Returns the document id."""
  obj_id = objectid.ObjectId()
  coll = db.Collection('document')
  doc = {'_id': obj_id,
         'content': content,
         'owner_uid': owner_uid,
         'domain_id': domain_id,
         'doc_type': doc_type,
         'doc_id': doc_id or obj_id,
         **kwargs}
  if parent_doc_type or parent_doc_id:
    assert parent_doc_type and parent_doc_id
    doc['parent_doc_type'], doc['parent_doc_id'] = parent_doc_type, parent_doc_id
  await coll.insert(doc)
  return doc['doc_id']


@argmethod.wrap
async def get(domain_id: str, doc_type: int, doc_id: convert_doc_id):
  coll = db.Collection('document')
  return await coll.find_one({'domain_id': domain_id,
                              'doc_type': doc_type,
                              'doc_id': doc_id})


async def set(domain_id: str, doc_type: int, doc_id: convert_doc_id, **kwargs):
  coll = db.Collection('document')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id},
                                   update={'$set': kwargs},
                                   new=True)
  return doc


def get_multi(domain_id, doc_type, *, fields=None, **kwargs):
  coll = db.Collection('document')
  return coll.find({'domain_id': domain_id, 'doc_type': doc_type, **kwargs}, fields=fields)


@argmethod.wrap
async def inc(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str, value: int):
  coll = db.Collection('document')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id},
                                   update={'$inc': {key: value}},
                                   new=True)
  return doc


@argmethod.wrap
async def push(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str,
               content: str, owner_uid: int, **kwargs):
  coll = db.Collection('document')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id},
                                   update={'$push': {key: {**kwargs,
                                                           'content': content,
                                                           'owner_uid': owner_uid,
                                                           'at': datetime.datetime.utcnow()}}},
                                   new=True)
  return doc


@argmethod.wrap
async def add_to_set(domain_id: str, doc_type: int, doc_id: convert_doc_id, set_key: str,
                     content):
  coll = db.Collection('document')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id},
                                   update={'$addToSet': {set_key: content}},
                                   new=True)
  return doc


@argmethod.wrap
async def pull(domain_id: str, doc_type: int, doc_id: convert_doc_id, set_key: str,
               contents):
  coll = db.Collection('document')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id},
                                   update={'$pull': {set_key: {'$in': contents}}},
                                   new=True)
  return doc


@argmethod.wrap
async def get_status(domain_id: str, doc_type: int, doc_id: convert_doc_id, uid: int, fields=None):
  coll = db.Collection('document.status')
  return await coll.find_one({'domain_id': domain_id, 'doc_type': doc_type,
                              'doc_id': doc_id, 'uid': uid},
                             fields)


def get_multi_status(domain_id, doc_type, *, fields=None, **kwargs):
  coll = db.Collection('document.status')
  return coll.find({'domain_id': domain_id, 'doc_type': doc_type, **kwargs}, fields=fields)


async def set_status(domain_id, doc_type, doc_id, uid, **kwargs):
  coll = db.Collection('document.status')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id,
                                          'uid': uid},
                                   update={'$set': kwargs},
                                   upsert=True,
                                   new=True)
  return doc


@argmethod.wrap
async def set_if_not_status(domain_id: str, doc_type: int, doc_id: convert_doc_id,
                            uid: int, key: str, value: int, if_not: int, **kwargs):
  coll = db.Collection('document.status')
  return await coll.find_and_modify(query={'domain_id': domain_id,
                                           'doc_type': doc_type,
                                           'doc_id': doc_id,
                                           'uid': uid,
                                           key: {'$not': {'$eq': if_not}}},
                                    update={'$set': {key: value, **kwargs}},
                                    upsert=True,
                                    new=True)


@argmethod.wrap
async def capped_inc_status(domain_id: str,
                            doc_type: int,
                            doc_id: convert_doc_id,
                            uid: int,
                            key: str,
                            value: int,
                            min_value: int = -1,
                            max_value: int = 1):
  assert value != 0
  if value > 0:
    not_expr = {'$gte': max_value}
  else:
    not_expr = {'$lte': min_value}
  coll = db.Collection('document.status')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id,
                                          'uid': uid,
                                          key: {'$not': not_expr}},
                                   update={'$inc': {key: value}},
                                   upsert=True,
                                   new=True)
  return doc


async def rev_push_status(domain_id, doc_type, doc_id, uid, key, value):
  coll = db.Collection('document.status')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id,
                                          'uid': uid},
                                   update={'$push': {key: value},
                                           '$inc': {'rev': 1}},
                                   upsert=True,
                                   new=True)
  return doc


async def rev_set_status(domain_id, doc_type, doc_id, uid, rev, **kwargs):
  coll = db.Collection('document.status')
  doc = await coll.find_and_modify(query={'domain_id': domain_id,
                                          'doc_type': doc_type,
                                          'doc_id': doc_id,
                                          'uid': uid,
                                          'rev': rev},
                                   update={'$set': kwargs},
                                   new=True)
  return doc


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('document')
  await coll.ensure_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('doc_id', 1)], unique=True)
  await coll.ensure_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('parent_doc_type', 1),
                           ('parent_doc_id', 1),
                           ('vote', -1),
                           ('doc_id', -1)], sparse=True)
  status_coll = db.Collection('document.status')
  await status_coll.ensure_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('uid', 1),
                                  ('doc_id', 1)], unique=True)
  # for rp system
  await status_coll.ensure_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('doc_id', 1),
                                  ('status', 1),
                                  ('rid', 1),
                                  ('rp', 1)], sparse=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
