import asyncio

from bson import objectid

from vj4 import error
from vj4.model import document
from vj4.util import argmethod
from vj4.util import validator


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int, dag=[]):
  validator.check_title(title)
  validator.check_content(content)
  return await document.add(domain_id, content, owner_uid, document.TYPE_TRAINING,
                            title=title, dag=dag, pids=list(pids))


@argmethod.wrap
async def get(domain_id: str, tid: objectid.ObjectId):
  tdoc = await document.get(domain_id, document.TYPE_TRAINING, tid)
  if not tdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_TRAINING, tid)
  return tdoc


async def edit(domain_id: str, tid: objectid.ObjectId, **kwargs):
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


async def _update_status(domain_id, tdoc, uid, key, value):
  tsdoc = await document.rev_push_status(domain_id, document.TYPE_TRAINING, tdoc['doc_id'],
                                         uid, key, value)
  done_pids = set(tsdoc.get('done_pids', []))
  done_tids = set(tsdoc.get('done_tids', []))
  done = done_pids.issuperset(tdoc['pids']) and done_tids.issuperset(tdoc['require_tids'])
  await document.rev_set_status(domain_id, document.TYPE_TRAINING, tdoc['doc_id'],
                                uid, tsdoc['rev'],
                                done_pids=list(done_pids), done_tids=list(done_tids), done=done)
  if done:
    await update_status_by_tid(domain_id, uid, tdoc['doc_id'])


@argmethod.wrap
async def update_status_by_pid(domain_id: str, uid: int, pid: document.convert_doc_id):
  tdocs = document.get_multi(domain_id=domain_id,
                             doc_type=document.TYPE_TRAINING,
                             pids=pid,
                             fields=['doc_id', 'pids', 'require_tids'])
  futs = []
  async for tdoc in tdocs:
    futs.append(_update_status(domain_id, tdoc, uid, 'done_pids', pid))
  await asyncio.gather(*futs)


@argmethod.wrap
async def update_status_by_tid(domain_id: str, uid: int, tid: objectid.ObjectId):
  tdocs = document.get_multi(domain_id=domain_id,
                             doc_type=document.TYPE_TRAINING,
                             require_tids=tid,
                             fields=['doc_id', 'pids', 'require_tids'])
  futs = []
  async for tdoc in tdocs:
    futs.append(_update_status(domain_id, tdoc, uid, 'done_tids', tid))
  await asyncio.gather(*futs)


if __name__ == '__main__':
  argmethod.invoke_by_args()
