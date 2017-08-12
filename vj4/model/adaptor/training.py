from bson import objectid
from pymongo import errors

from vj4 import error
from vj4.model import document
from vj4.util import argmethod
from vj4.util import validator


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int, dag=[], desc=''):
  validator.check_title(title)
  validator.check_intro(content)
  validator.check_description(desc)
  dag = list(dag)
  for node in dag:
    for nid in node['require_nids']:
      if nid >= node['_id']:
        raise error.ValidationError('dag')
  return await document.add(domain_id, content, owner_uid, document.TYPE_TRAINING,
                            title=title, dag=dag, desc=desc, enroll=0)


@argmethod.wrap
async def get(domain_id: str, tid: objectid.ObjectId):
  tdoc = await document.get(domain_id, document.TYPE_TRAINING, tid)
  if not tdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_TRAINING, tid)
  return tdoc


async def edit(domain_id: str, tid: objectid.ObjectId, **kwargs):
  if 'title' in kwargs:
      validator.check_title(kwargs['title'])
  if 'content' in kwargs:
      validator.check_intro(kwargs['content'])
  if 'desc' in kwargs:
      validator.check_description(kwargs['desc'])
  if 'dag' in kwargs:
    kwargs['dag'] = list(kwargs['dag'])
    for node in kwargs['dag']:
      for nid in node['require_nids']:
        if nid >= node['_id']:
          raise error.ValidationError('dag')
  return await document.set(domain_id, document.TYPE_TRAINING, tid, **kwargs)


@argmethod.wrap
async def get_status(domain_id: str, tid: objectid.ObjectId, uid: int, fields=None):
  return await document.get_status(domain_id, document.TYPE_TRAINING, tid, uid, fields=fields)


async def set_status(domain_id: str, tid: objectid.ObjectId, uid: int, **kwargs):
  return await document.set_status(domain_id, document.TYPE_TRAINING, tid, uid, **kwargs)


def get_multi_status(*, fields=None, **kwargs):
  return document.get_multi_status(doc_type=document.TYPE_TRAINING, fields=fields, **kwargs)


async def get_dict_status(domain_id, uid, tids, *, fields=None):
  result = dict()
  async for tsdoc in get_multi_status(domain_id=domain_id,
                                      uid=uid,
                                      doc_id={'$in': list(set(tids))},
                                      fields=fields):
    result[tsdoc['doc_id']] = tsdoc
  return result


def get_multi(domain_id: str, *, fields=None, **kwargs):
  return document.get_multi(domain_id=domain_id, doc_type=document.TYPE_TRAINING,
                            fields=fields, **kwargs)


@argmethod.wrap
async def enroll(domain_id: str, tid: objectid.ObjectId, uid: int):
  try:
    await document.capped_inc_status(domain_id, document.TYPE_TRAINING, tid,
                                     uid, 'enroll', 1, 0, 1)
  except errors.DuplicateKeyError:
    raise error.TrainingAlreadyEnrollError(domain_id, tid, uid) from None
  return await document.inc(domain_id, document.TYPE_TRAINING, tid, 'enroll', 1)


async def get_dict(domain_id, tids, *, fields=None):
  result = dict()
  async for tdoc in get_multi(domain_id=domain_id,
                              doc_id={'$in': list(set(tids))},
                              fields=fields):
    result[tdoc['doc_id']] = tdoc
  return result


if __name__ == '__main__':
  argmethod.invoke_by_args()
