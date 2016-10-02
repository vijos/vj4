import asyncio
from bson import objectid

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
  for node in dag:
    for nid in node['require_nids']:
      if nid >= node['_id']:
        raise error.ValidationError('dag')
  return await document.add(domain_id, content, owner_uid, document.TYPE_TRAINING,
                            title=title, dag=dag, pids=list(pids))


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
    for node in kwargs['dag']:
      for nid in node['require_nids']:
        if nid >= node['_id']:
          raise error.ValidationError('dag')
  return await document.set(domain_id, document.TYPE_TRAINING, tid, **kwargs)


@argmethod.wrap
async def get_status(domain_id: str, tid: objectid.ObjectId, uid: int, fields=None):
  return await document.get_status(domain_id, document.TYPE_TRAINING, tid, uid, fields=fields)


@argmethod.wrap
async def check(domain_id: str, tid: objectid.ObjectId, uid: int):
  tdoc = await get(domain_id, tid)
  done_count = await document.get_multi_status(domain_id=domain_id,
                                               doc_type=document.TYPE_TRAINING,
                                               uid=uid,
                                               done=True,
                                               doc_id={'$in': tdoc['require_tids']}).count()
  if done_count < len(tdoc['require_tids']):
    raise error.TrainingRequirementNotSatisfiedError(domain_id, document.TYPE_TRAINING, tid)
  return tdoc


@argmethod.wrap
async def get_list_by_user(domain_id: str, uid: int, *, fields=None):
  tsdocs = document.get_multi_status(domain_id=domain_id,
                                     doc_type=document.TYPE_TRAINING,
                                     uid=uid, done=True, fields=['doc_id'])
  done_tids = []
  async for tsdoc in tsdocs:
    done_tids.append(tsdoc['doc_id'])
  # TODO(iceboy): pagination, projection.
  tdocs = await (document.get_multi(domain_id=domain_id,
                                    doc_type=document.TYPE_TRAINING,
                                    require_tids={'$not': {'$elemMatch': {'$nin': done_tids}}},
                                    fields=fields)
                 .sort([('doc_id', 1)])
                 .to_list(None))
  return tdocs


def get_multi(domain_id: str, *, fields=None, **kwargs):
  return document.get_multi(domain_id=domain_id, doc_type=document.TYPE_TRAINING,
                            fields=fields, **kwargs)


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


if __name__ == '__main__':
  argmethod.invoke_by_args()
