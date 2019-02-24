import itertools
from bson import objectid
from pymongo import ReturnDocument

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
TYPE_USERFILE = 50
TYPE_HOMEWORK = 60

DOC_ID_DISCUSSION_NODES = 1

PROJECTION_PUBLIC = {
  'doc_type': 1,
  'doc_id': 1,
  'parent_doc_type': 1,
  'parent_doc_id': 1,
  'title': 1,
  'hidden': 1
}


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
  coll = db.coll('document')
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
  await coll.insert_one(doc)
  return doc['doc_id']


@argmethod.wrap
async def get(domain_id: str, doc_type: int, doc_id: convert_doc_id, fields=None):
  coll = db.coll('document')
  return await coll.find_one({'domain_id': domain_id,
                              'doc_type': doc_type,
                              'doc_id': doc_id}, projection=fields)


async def set(domain_id: str, doc_type: int, doc_id: convert_doc_id, **kwargs):
  coll = db.coll('document')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$set': kwargs},
                                       return_document=ReturnDocument.AFTER)
  return doc


async def delete(domain_id: str, doc_type: int, doc_id: convert_doc_id):
  # TODO(twd2): delete status?
  coll = db.coll('document')
  return await coll.delete_one({'domain_id': domain_id,
                                'doc_type': doc_type,
                                'doc_id': doc_id})


async def delete_multi(domain_id: str, doc_type: int, **kwargs):
  # TODO(twd2): delete status?
  coll = db.coll('document')
  return await coll.delete_many({'domain_id': domain_id,
                                 'doc_type': doc_type,
                                 **kwargs})


def get_multi(*, fields=None, **kwargs):
  coll = db.coll('document')
  return coll.find(kwargs, projection=fields)


async def get_dict(domain_id: str, dtuples, *, fields=None):
  query = {'$or': []}
  for doc_type, doc_tuples in itertools.groupby(sorted(dtuples), key=lambda e: e[0]):
    query['$or'].append({'domain_id': domain_id, 'doc_type': doc_type,
                         'doc_id': {'$in': [e[1] for e in doc_tuples]}})
  result = dict()
  if not query['$or']:
    return result
  async for doc in get_multi(**query, fields=fields).hint([('domain_id', 1),
                                                           ('doc_type', 1),
                                                           ('doc_id', 1)]):
    result[(doc['doc_type'], doc['doc_id'])] = doc
  return result


@argmethod.wrap
async def inc(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str, value: int):
  coll = db.coll('document')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$inc': {key: value}},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def inc_and_set(domain_id: str, doc_type: int, doc_id: convert_doc_id,
                      inc_key: str, inc_value: int, set_key: str, set_value: lambda _: _):
  coll = db.coll('document')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$inc': {inc_key: inc_value},
                                               '$set': {set_key: set_value}},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def push(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str,
               content: str, owner_uid: int, **kwargs):
  coll = db.coll('document')
  obj_id = objectid.ObjectId()
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$push': {key: {**kwargs,
                                                               'content': content,
                                                               'owner_uid': owner_uid,
                                                               '_id': obj_id}}},
                                       return_document=ReturnDocument.AFTER)
  return doc, obj_id


@argmethod.wrap
async def delete_sub(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str,
                     sub_id: objectid.ObjectId):
  coll = db.coll('document')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$pull': {key: {'_id': sub_id}}},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def get_sub(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str,
                  sub_id: objectid.ObjectId):
  coll = db.coll('document')
  doc = await coll.find_one({'domain_id': domain_id,
                             'doc_type': doc_type,
                             'doc_id': doc_id,
                             key: {'$elemMatch': {'_id': sub_id}}})
  if not doc:
    return None, None
  for sdoc in doc.get(key, []):
    if sdoc['_id'] == sub_id:
      return doc, sdoc
  return doc, None


@argmethod.wrap
async def set_sub(domain_id: str, doc_type: int, doc_id: convert_doc_id, key: str,
                  sub_id: objectid.ObjectId, **kwargs):
  coll = db.coll('document')
  mod = dict(('{0}.$.{1}'.format(key, k), v) for k, v in kwargs.items())
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id,
                                               key: {'$elemMatch': {'_id': sub_id}}},
                                       update={'$set': mod},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def add_to_set(domain_id: str, doc_type: int, doc_id: convert_doc_id, set_key: str,
                     content):
  coll = db.coll('document')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$addToSet': {set_key: content}},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def pull(domain_id: str, doc_type: int, doc_id: convert_doc_id, set_key: str,
               contents):
  coll = db.coll('document')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id},
                                       update={'$pull': {set_key: {'$in': contents}}},
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def get_status(domain_id: str, doc_type: int, doc_id: convert_doc_id, uid: int,
                     *, fields=None):
  coll = db.coll('document.status')
  return await coll.find_one({'domain_id': domain_id, 'doc_type': doc_type,
                              'doc_id': doc_id, 'uid': uid},
                             projection=fields)


def get_multi_status(*, fields=None, **kwargs):
  coll = db.coll('document.status')
  return coll.find(kwargs, projection=fields)


async def set_status(domain_id, doc_type, doc_id, uid, **kwargs):
  coll = db.coll('document.status')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id,
                                               'uid': uid},
                                       update={'$set': kwargs},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def set_if_not_status(domain_id: str, doc_type: int, doc_id: convert_doc_id,
                            uid: int, key: str, value: int, if_not: int, **kwargs):
  coll = db.coll('document.status')
  return await coll.find_one_and_update(filter={'domain_id': domain_id,
                                                'doc_type': doc_type,
                                                'doc_id': doc_id,
                                                'uid': uid,
                                                key: {'$not': {'$eq': if_not}}},
                                        update={'$set': {key: value, **kwargs}},
                                        upsert=True,
                                        return_document=ReturnDocument.AFTER)


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
  coll = db.coll('document.status')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id,
                                               'uid': uid,
                                               key: {'$not': not_expr}},
                                       update={'$inc': {key: value}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
  return doc


@argmethod.wrap
async def inc_status(domain_id: str, doc_type: int, doc_id: convert_doc_id, uid: int,
                     key: str, value: int):
  coll = db.coll('document.status')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id,
                                               'uid': uid},
                                       update={'$inc': {key: value}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
  return doc


async def rev_push_status(domain_id, doc_type, doc_id, uid, key, value):
  coll = db.coll('document.status')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id,
                                               'uid': uid},
                                       update={'$push': {key: value},
                                               '$inc': {'rev': 1}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
  return doc


async def rev_init_status(domain_id, doc_type, doc_id, uid):
  coll = db.coll('document.status')
  doc = await coll.find_one_and_update(filter={'domain_id': domain_id,
                                               'doc_type': doc_type,
                                               'doc_id': doc_id,
                                               'uid': uid},
                                       update={'$inc': {'rev': 1}},
                                       upsert=True,
                                       return_document=ReturnDocument.AFTER)
  return doc


async def rev_set_status(domain_id, doc_type, doc_id, uid, rev, return_doc=True, **kwargs):
  coll = db.coll('document.status')
  filter = {'domain_id': domain_id,
            'doc_type': doc_type,
            'doc_id': doc_id,
            'uid': uid,
            'rev': rev}
  update = {'$set': kwargs,
            '$inc': {'rev': 1}}
  if return_doc:
    doc = await coll.find_one_and_update(filter=filter, update=update,
                                         return_document=ReturnDocument.AFTER)
    return doc
  else:
    result = await coll.update_one(filter, update)
    return result


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('document')
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('doc_id', 1)], unique=True)
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('owner_uid', 1),
                           ('doc_id', -1)])
  # for problem
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('category', 1),
                           ('doc_id', 1)], sparse=True)
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('hidden', 1),
                           ('category', 1),
                           ('doc_id', 1)], sparse=True)
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('tag', 1),
                           ('doc_id', 1)], sparse=True)
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('hidden', 1),
                           ('tag', 1),
                           ('doc_id', 1)], sparse=True)
  # for problem solution
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('parent_doc_type', 1),
                           ('parent_doc_id', 1),
                           ('vote', -1),
                           ('doc_id', -1)], sparse=True)
  # for discussion
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('update_at', -1),
                           ('doc_id', -1)], sparse=True)
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('parent_doc_type', 1),
                           ('parent_doc_id', 1),
                           ('update_at', -1),
                           ('doc_id', -1)], sparse=True)
  # hidden doc
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('hidden', 1),
                           ('doc_id', -1)], sparse=True)
  # for contest
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('pids', 1)], sparse=True)
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('rule', 1),
                           ('doc_id', -1)], sparse=True)
  # for training
  await coll.create_index([('domain_id', 1),
                           ('doc_type', 1),
                           ('dag.pids', 1)], sparse=True)
  status_coll = db.coll('document.status')
  await status_coll.create_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('uid', 1),
                                  ('doc_id', 1)], unique=True)
  # for rp system
  await status_coll.create_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('doc_id', 1),
                                  ('status', 1),
                                  ('rid', 1),
                                  ('rp', 1)], sparse=True)
  # for contest rule OI
  await status_coll.create_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('doc_id', 1),
                                  ('score', -1)], sparse=True)
  # for contest rule ACM
  await status_coll.create_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('doc_id', 1),
                                  ('accept', -1),
                                  ('time', 1)], sparse=True)
  # for training
  await status_coll.create_index([('domain_id', 1),
                                  ('doc_type', 1),
                                  ('uid', 1),
                                  ('enroll', 1),
                                  ('doc_id', 1)], sparse=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
