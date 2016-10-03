import asyncio
from bson import objectid
from pymongo import errors

from vj4 import constant
from vj4 import error
from vj4.model import document
from vj4.model.adaptor import problem
from vj4.util import argmethod
from vj4.util import validator


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int, dag=[]):
  validator.check_title(title)
  validator.check_content(content)
  dag = list(dag)
  for node in dag:
    for nid in node['require_nids']:
      if nid >= node['_id']:
        raise error.ValidationError('dag')
  return await document.add(domain_id, content, owner_uid, document.TYPE_TRAINING,
                            title=title, dag=dag, enroll=0)


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
      validator.check_content(kwargs['content'])
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


# TODO(twd2): move to jobs
@argmethod.wrap
async def update_status(domain_id: str, tid: objectid.ObjectId, uid: int, done_pids=None):
  tdoc = await get(domain_id, tid)
  tsdoc = await get_status(domain_id, tdoc['doc_id'], uid)
  pids = set()
  for node in tdoc['dag']:
    for pid in node['pids']:
      pids.add(pid)
  if done_pids is None:
    psdict = await problem.get_dict_status(domain_id, uid, pids)
    done_pids = set()
    for pid, psdoc in psdict.items():
      if 'status' in psdoc:
        if psdoc['status'] == constant.record.STATUS_ACCEPTED:
          done_pids.add(pid)
  done_pids = set(done_pids)
  done_nids = set()
  sorted_dag = sorted(tdoc['dag'], key=lambda n: n['_id'])
  for node in sorted_dag:
    if done_nids >= set(node['require_nids']) and done_pids >= set(node['pids']):
      done_nids.add(node['_id'])
  done = len(done_nids) == len(tdoc['dag'])
  await document.rev_set_status(domain_id, document.TYPE_TRAINING, tdoc['doc_id'],
                                uid, tsdoc['rev'],
                                done_nids=list(done_nids), done=done)


async def _update_status(domain_id, tdoc, uid, key, value):
  tsdoc = await document.rev_push_status(domain_id, document.TYPE_TRAINING, tdoc['doc_id'],
                                         uid, key, value)
  done_pids = set(tsdoc.get('done_pids', []))
  done_nids = set()
  sorted_dag = sorted(tdoc['dag'], key=lambda n: n['_id'])
  for node in sorted_dag:
    if done_nids >= set(node['require_nids']) and done_pids >= set(node['pids']):
      done_nids.add(node['_id'])
  done = len(done_nids) == len(tdoc['dag'])
  await document.rev_set_status(domain_id, document.TYPE_TRAINING, tdoc['doc_id'],
                                uid, tsdoc['rev'],
                                done_nids=list(done_nids), done=done)


@argmethod.wrap
async def update_status_by_pid(domain_id: str, uid: int, pid: document.convert_doc_id):
  tdocs = document.get_multi(domain_id=domain_id,
                             doc_type=document.TYPE_TRAINING,
                             **{'dag.pids': pid},
                             fields=['doc_id', 'dag'])
  futs = []
  async for tdoc in tdocs:
    futs.append(_update_status(domain_id, tdoc, uid, 'done_pids', pid))
  await asyncio.gather(*futs)


async def get_dict(domain_id, tids, *, fields=None):
  result = dict()
  async for tdoc in get_multi(domain_id=domain_id,
                              doc_id={'$in': list(set(tids))},
                              fields=fields):
    result[tdoc['doc_id']] = tdoc
  return result


if __name__ == '__main__':
  argmethod.invoke_by_args()
