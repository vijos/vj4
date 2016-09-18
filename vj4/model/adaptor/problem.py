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
              pid: document.convert_doc_id=None, data: objectid.ObjectId=None,
              hidden: bool=False):
  validator.check_title(title)
  validator.check_content(content)
  return await document.add(domain_id, content, owner_uid,
                            document.TYPE_PROBLEM, pid, title=title, data=data,
                            hidden=hidden, num_submit=0, num_accept=0)


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
async def edit(domain_id: str, pid: document.convert_doc_id, **kwargs):
  if 'title' in kwargs:
      validator.check_title(kwargs['title'])
  if 'content' in kwargs:
      validator.check_content(kwargs['content'])
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, **kwargs)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  return pdoc


@argmethod.wrap
async def count(domain_id: str, **kwargs):
  return await document.get_multi(domain_id=domain_id, doc_type=document.TYPE_PROBLEM,
                                  **kwargs).count()


def get_multi(*, fields=None, **kwargs):
  return document.get_multi(doc_type=document.TYPE_PROBLEM, fields=fields, **kwargs)


async def get_dict(pdom_and_ids, *, fields=None):
  pquery = {'$or': [{'domain_id': e[0], 'doc_id': e[1]} for e in set(pdom_and_ids)]}
  result = dict()
  async for pdoc in get_multi(**pquery, fields=fields).hint([('domain_id', 1),
                                                             ('doc_type', 1),
                                                             ('doc_id', 1)]):
    result[(pdoc['domain_id'], pdoc['doc_id'])] = pdoc
  return result


@argmethod.wrap
async def get_status(domain_id: str, pid: document.convert_doc_id, uid: int, fields=None):
  return await document.get_status(domain_id, document.TYPE_PROBLEM, pid, uid, fields=fields)


def get_multi_status(*, fields=None, **kwargs):
  return document.get_multi_status(doc_type=document.TYPE_PROBLEM, fields=fields, **kwargs)


async def get_dict_status(domain_id, uid, pids, *, fields=None):
  result = dict()
  async for psdoc in get_multi_status(domain_id=domain_id,
                                      uid=uid,
                                      doc_id={'$in': list(set(pids))},
                                      fields=fields):
    result[psdoc['doc_id']] = psdoc
  return result


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


def get_multi_solution(domain_id: str, pid: document.convert_doc_id, fields=None):
  return document.get_multi(domain_id=domain_id,
                            doc_type=document.TYPE_PROBLEM_SOLUTION,
                            parent_doc_type=document.TYPE_PROBLEM,
                            parent_doc_id=pid,
                            fields=fields) \
                 .sort([('vote', -1), ('doc_id', -1)])


@argmethod.wrap
async def get_list_solution(domain_id: str, pid: document.convert_doc_id,
                            fields=None, skip: int = 0, limit: int = 0):
  return await document.get_multi(domain_id=domain_id,
                                  doc_type=document.TYPE_PROBLEM_SOLUTION,
                                  parent_doc_type=document.TYPE_PROBLEM,
                                  parent_doc_id=pid,
                                  fields=fields) \
                       .sort([('vote', -1), ('doc_id', -1)]) \
                       .skip(skip) \
                       .limit(limit) \
                       .to_list(None)


@argmethod.wrap
async def get_solution_status(domain_id: str, psid: document.convert_doc_id, uid: int):
  return await document.get_status(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, uid)


async def get_dict_solution_status(dom_and_ids, uid, *, fields=None):
  query = {
    'doc_type': document.TYPE_PROBLEM_SOLUTION,
    'uid': uid,
    '$or': [{'domain_id': e[0], 'doc_id': e[1]} for e in set(dom_and_ids)],
  }
  result = dict()
  async for pssdoc in document.get_multi_status(**query, fields=fields):
    result[(pssdoc['domain_id'], pssdoc['doc_id'])] = pssdoc
  return result


@argmethod.wrap
async def vote_solution(domain_id: str, psid: document.convert_doc_id, uid: int, value: int):
  try:
    pssdoc = await document.capped_inc_status(domain_id, document.TYPE_PROBLEM_SOLUTION, psid,
                                              uid, 'vote', value)
  except errors.DuplicateKeyError:
    raise error.AlreadyVotedError(domain_id, psid, uid) from None
  psdoc = await document.inc(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, 'vote', value)
  return psdoc, pssdoc


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
async def set_hidden(domain_id: str, pid: document.convert_doc_id, hidden: bool):
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, hidden=hidden)
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

  return list(set(pids))


@argmethod.wrap
async def inc(domain_id: str, pid: document.convert_doc_id, key: str, value: int):
  return await document.inc(domain_id, document.TYPE_PROBLEM, pid, key, value)


@argmethod.wrap
async def update_status(domain_id: str, pid: document.convert_doc_id, uid: int,
                        rid: objectid.ObjectId, status: int):
  try:
    return await document.set_if_not_status(domain_id, document.TYPE_PROBLEM, pid, uid,
                                            'status', status, constant.record.STATUS_ACCEPTED,
                                            rid=rid)
  except errors.DuplicateKeyError:
    return None


if __name__ == '__main__':
  argmethod.invoke_by_args()
