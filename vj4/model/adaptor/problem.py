import builtins
import datetime
import itertools

from bson import objectid
from pymongo import errors

from vj4 import constant
from vj4 import db
from vj4 import error
from vj4.model import document
from vj4.model import fs
from vj4.util import argmethod


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int,
              pid: document.convert_doc_id = None, data: objectid.ObjectId = None):
  return await document.add(domain_id, content, owner_uid,
                            document.TYPE_PROBLEM, pid, title=title, data=data)


@argmethod.wrap
async def get(domain_id: str, pid: document.convert_doc_id, uid: int = None):
  pdoc = await document.get(domain_id, document.TYPE_PROBLEM, pid)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  if uid is not None:
    pdoc['psdoc'] = await document.get_status(domain_id, document.TYPE_PROBLEM,
                                              doc_id=pid, uid=uid)
  else:
    pdoc['psdoc'] = None
  return pdoc


@argmethod.wrap
async def set(domain_id: str, pid: document.convert_doc_id, **kwargs):
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, **kwargs)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  return pdoc


@argmethod.wrap
async def count(domain_id: str):
  return await document.get_multi(domain_id, document.TYPE_PROBLEM).count()


@argmethod.wrap
async def get_list(domain_id: str, uid: int = None, fields=None, skip: int = 0, limit: int = 0):
  # TODO(iceboy): projection.
  pdocs = await (document.get_multi(domain_id, document.TYPE_PROBLEM, fields=fields)
                 .sort([('doc_id', 1)])
                 .skip(skip)
                 .limit(limit)
                 .to_list(None))
  piter = iter(pdocs)
  if uid is not None:
    doc_ids = [pdoc['doc_id'] for pdoc in pdocs]
    # TODO(iceboy): projection.
    psdocs = (document.get_multi_status(domain_id, document.TYPE_PROBLEM,
                                        uid=uid, doc_id={'$in': doc_ids})
              .sort([('doc_id', 1)]))
    async for psdoc in psdocs:
      pdoc = next(piter)
      while pdoc['doc_id'] != psdoc['doc_id']:
        pdoc['psdoc'] = {}
        pdoc = next(piter)
      pdoc['psdoc'] = psdoc
  for rest in piter:
    rest['psdoc'] = {}
  return pdocs


@argmethod.wrap
async def set_star(domain_id: str, pid: document.convert_doc_id, uid: int, star: bool):
  return await document.set_status(domain_id, document.TYPE_PROBLEM, pid, uid, star=star)


@argmethod.wrap
async def add_solution(domain_id: str, pid: document.convert_doc_id, uid: int, content: str):
  return await document.add(domain_id, content, uid, document.TYPE_PROBLEM_SOLUTION, None,
                            document.TYPE_PROBLEM, pid, vote=0, reply=[])


@argmethod.wrap
async def get_solution(domain_id: str, psid: document.convert_doc_id, pid=None):
  psdoc = await document.get(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
  if not psdoc or (pid and psdoc['parent_doc_id'] != pid):
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
  return psdoc


@argmethod.wrap
async def get_list_solution(domain_id: str, pid: document.convert_doc_id,
                            fields=None, skip: int = 0, limit: int = 0):
  return await (document.get_multi(domain_id, document.TYPE_PROBLEM_SOLUTION,
                                     parent_doc_type=document.TYPE_PROBLEM, parent_doc_id=pid,
                                     fields=fields)
                .sort([('vote', -1), ('doc_id', -1)])
                .skip(skip)
                .limit(limit)
                .to_list(None))


@argmethod.wrap
async def vote_solution(domain_id: str, psid: document.convert_doc_id, uid: int, value: int):
  try:
    await document.capped_inc_status(domain_id, document.TYPE_PROBLEM_SOLUTION, psid,
                                     uid, 'vote', value)
  except errors.DuplicateKeyError:
    raise error.AlreadyVotedError(domain_id, psid, uid) from None
  return await document.inc(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, 'vote', value)


@argmethod.wrap
async def reply_solution(domain_id: str, psid: document.convert_doc_id, uid: int, content: str):
  return await document.push(domain_id, document.TYPE_PROBLEM_SOLUTION, psid,
                             'reply', content, uid)


async def get_data(domain_id, pid):
  pdoc = await get(domain_id, pid)
  if not pdoc['data']:
    raise error.ProblemDataNotFoundError(domain_id, pid)
  return await fs.get(pdoc['data'])


@argmethod.wrap
async def get_data_md5(domain_id: str, pid: document.convert_doc_id):
  pdoc = await get(domain_id, pid)
  if not pdoc['data']:
    raise error.ProblemDataNotFoundError(domain_id, pid)
  return await fs.get_md5(pdoc['data'])


@argmethod.wrap
async def set_data(domain_id: str, pid: document.convert_doc_id, data: objectid.ObjectId):
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, data=data)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  return pdoc


@argmethod.wrap
async def get_data_list(last: int):
  last_datetime = datetime.datetime.fromtimestamp(last)
  # TODO(twd2): performance improve, more elegant
  coll = db.Collection('document')
  cursor = coll.find({'doc_type': document.TYPE_PROBLEM})
  pids = []  # with domain_id
  async for pdoc in cursor:
    if 'data' not in pdoc or not pdoc['data']:
      continue
    date = await fs.get_datetime(pdoc['data'])
    if not date:
      continue
    if last_datetime < date:
      pids.append((pdoc['domain_id'], pdoc['doc_id']))

  return list(builtins.set(pids))


@argmethod.wrap
async def update_status(domain_id: str, pid: document.convert_doc_id, uid: int,
                        rid: objectid.ObjectId, status: int):
  try:
    await document.set_if_not_status(domain_id, document.TYPE_PROBLEM, pid, uid,
                                     'status', status, constant.record.STATUS_ACCEPTED, rid=rid)
  except errors.DuplicateKeyError:
    pass


async def attach_pdocs(docs, domain_field_name, pid_field_name):
  """Attach udoc to docs by uid in the specified field."""
  # TODO(iceboy): projection.
  pids_by_domain = {}
  for domain_id, domain_docs in itertools.groupby(docs, lambda doc: doc[domain_field_name]):
    pids = builtins.set(doc[pid_field_name] for doc in domain_docs)
    pdocs = await document.get_multi(domain_id, document.TYPE_PROBLEM,
                                     doc_id={'$in': list(pids)}).to_list(None)
    pids_by_domain[domain_id] = dict((pdoc['doc_id'], pdoc) for pdoc in pdocs)
  for doc in docs:
    doc['pdoc'] = pids_by_domain[doc[domain_field_name]].get(doc[pid_field_name])
  return docs


if __name__ == '__main__':
  argmethod.invoke_by_args()
