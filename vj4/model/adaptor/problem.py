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
from vj4.util import validator


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int,
              pid: document.convert_doc_id = None, data: objectid.ObjectId = None):
  validator.check_title(title)
  validator.check_content(content)
  return await document.add(domain_id, content, owner_uid,
                            document.TYPE_PROBLEM, pid, title=title, data=data,
                            num_submit=0, num_accept=0)


@argmethod.wrap
async def get(domain_id: str, pid: document.convert_doc_id, uid: int = None):
  pdoc = await document.get(domain_id, document.TYPE_PROBLEM, pid)
  if not pdoc:
    raise error.ProblemNotFoundError(domain_id, pid)
  # TODO(twd2): move out:
  if uid is not None:
    pdoc['psdoc'] = await document.get_status(domain_id, document.TYPE_PROBLEM,
                                              doc_id=pid, uid=uid)
  else:
    pdoc['psdoc'] = None
  return pdoc


@argmethod.wrap
async def set(domain_id: str, pid: document.convert_doc_id, **kwargs):
  if 'title' in kwargs:
      validator.check_title(kwargs['title'])
  if 'content' in kwargs:
      validator.check_content(kwargs['content'])
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, **kwargs)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  return pdoc


@argmethod.wrap
async def count(domain_id: str):
  return await document.get_multi(domain_id, document.TYPE_PROBLEM).count()


def get_multi(domain_id: str, fields=None, **kwargs):
  return document.get_multi(domain_id, document.TYPE_PROBLEM, fields=fields, **kwargs)


def get_multi_status(domain_id: str, *, fields=None, **kwargs):
  return document.get_multi_status(domain_id, document.TYPE_PROBLEM, fields=fields, **kwargs)


@argmethod.wrap
async def get_list(domain_id: str, uid: int=None, fields=None, skip: int=0, limit: int=0,
                   **kwargs):
  # TODO(iceboy): projection.
  pdocs = await (document.get_multi(domain_id, document.TYPE_PROBLEM, fields=fields, **kwargs)
                 .sort([('doc_id', 1)])
                 .skip(skip)
                 .limit(limit)
                 .to_list(None))
  piter = iter(pdocs)
  # TODO(twd2): move out:
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
  validator.check_content(content)
  return await document.add(domain_id, content, uid, document.TYPE_PROBLEM_SOLUTION, None,
                            document.TYPE_PROBLEM, pid, vote=0, reply=[])


@argmethod.wrap
async def get_solution(domain_id: str, psid: document.convert_doc_id, pid=None):
  psdoc = await document.get(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
  if not psdoc or (pid and psdoc['parent_doc_id'] != pid):
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
  return psdoc


@argmethod.wrap
async def set_solution(domain_id: str, psid: document.convert_doc_id, content: str):
  validator.check_content(content)
  psdoc = await document.set(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, content=content)
  if not psdoc:
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
async def get_solution_status(domain_id: str, psid: document.convert_doc_id, uid: int):
  return await document.get_status(domain_id, document.TYPE_PROBLEM_SOLUTION,
                                   psid, uid)


async def attach_pssdocs(docs, domain_field_name, psid_field_name, uid):
  """Attach pssdoc to docs by domain_id and psid in the specified field."""
  # TODO(twd2): projection.
  psids_by_domain = {}
  for domain_id, domain_docs in itertools.groupby(docs, lambda doc: doc[domain_field_name]):
    psids = builtins.set(doc[psid_field_name] for doc in domain_docs)
    pssdocs = await document.get_multi_status(domain_id, document.TYPE_PROBLEM_SOLUTION,
                                              doc_id={'$in': list(psids)}, uid=uid).to_list(None)
    psids_by_domain[domain_id] = dict((pssdoc['doc_id'], pssdoc) for pssdoc in pssdocs)
  for doc in docs:
    doc['pssdoc'] = psids_by_domain[doc[domain_field_name]].get(doc[psid_field_name])
  return docs


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
  validator.check_content(content)
  return await document.push(domain_id, document.TYPE_PROBLEM_SOLUTION, psid,
                             'reply', content, uid)


async def get_data(domain_id, pid):
  pdoc = await get(domain_id, pid)
  if not pdoc.get('data', None):
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
async def inc(domain_id: str, pid: document.convert_doc_id,
              submit: int, accept: int):
  await document.inc(domain_id, document.TYPE_PROBLEM, pid, 'num_submit', submit)
  pdoc = await document.inc(domain_id, document.TYPE_PROBLEM, pid, 'num_accept', accept)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  return pdoc


def _sort_and_uniquify(journal):
  # Sort and uniquify journal of the contest status document, by rid.
  key_func = lambda j: j['rid']
  return [list(g)[-1]
          for _, g in itertools.groupby(sorted(journal, key=key_func), key=key_func)]


def _stat_func(journal):
  stat = {'num_submit': 0, 'num_accept': 0}
  if not journal:
    return stat
  best_j = journal[-1]
  for j in journal:
    stat['num_submit'] += 1
    if j['accept']:
      stat['num_accept'] += 1
      best_j = j
      # ignore older record
      break
  stat['rid'] = best_j['rid']
  stat['status'] = best_j['status']
  return stat


@argmethod.wrap
async def update_status(domain_id: str, pid: document.convert_doc_id, uid: int,
                        rid: objectid.ObjectId, status: int, accept: bool, score: int):
  """This method returns None when the modification has been superseded by a parallel operation."""
  pdoc = await document.get(domain_id, document.TYPE_PROBLEM, pid)
  psdoc = await document.rev_push_status(
    domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], uid,
    'journal', {'rid': rid, 'accept': accept, 'status': status, 'score': score})
  new_journal = _sort_and_uniquify(psdoc['journal'])
  new_stats = _stat_func(new_journal)
  psdoc['journal'].pop()
  old_journal = _sort_and_uniquify(psdoc['journal'])
  old_stats = _stat_func(old_journal)
  psdoc = await document.rev_set_status(domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], uid,
                                        psdoc['rev'], journal=new_journal, **new_stats)
  # Deltas shouldn't be 0 even if rev_set_status failed (returned None)
  # because rev_push_status succeeded.
  return (psdoc,
          (new_stats['num_submit'] - old_stats['num_submit']),
          (new_stats['num_accept'] - old_stats['num_accept']))


async def attach_pdocs(docs, domain_field_name, pid_field_name):
  """Attach pdoc to docs by pid in the specified field."""
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
