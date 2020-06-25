import collections
import datetime
import itertools
import random
from bson import objectid
from pymongo import errors

from vj4 import constant
from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.service import bus
from vj4.util import argmethod
from vj4.util import validator


SETTING_DIFFICULTY_ALGORITHM = 0
SETTING_DIFFICULTY_ADMIN = 1
SETTING_DIFFICULTY_AVERAGE = 2

SETTING_DIFFICULTY_RANGE = collections.OrderedDict([
  (SETTING_DIFFICULTY_ALGORITHM, 'Use algorithm calculated'),
  (SETTING_DIFFICULTY_ADMIN, 'Use admin specificed'),
  (SETTING_DIFFICULTY_AVERAGE, 'Use average of above')
])


@argmethod.wrap
def get_categories():
  return builtin.PROBLEM_CATEGORIES


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int,
              pid: document.convert_doc_id=None, data: objectid.ObjectId=None,
              category: list=[], tag: list=[], hidden: bool=False, ac_msg=''):
  validator.check_title(title)
  validator.check_content(content)
  pid = await document.add(domain_id, content, owner_uid, document.TYPE_PROBLEM,
                           pid, title=title, data=data, category=category, tag=tag,
                           hidden=hidden, num_submit=0, num_accept=0, ac_msg=ac_msg)
  await domain.inc_user(domain_id, owner_uid, num_problems=1)
  return pid


async def copy(pdoc, dest_domain_id: str, owner_uid: int,
               pid: document.convert_doc_id=None, hidden: bool=False):
  # This copies contents only, and the data will be linked to the source problem.
  data = pdoc['data']
  src_domain_id, src_pid = pdoc['domain_id'], pdoc['doc_id']
  if type(data) is dict:
    src_domain_id, src_pid = data['domain'], data['pid']
  else:
    data = {'domain': src_domain_id, 'pid': src_pid}
  pid = await add(domain_id=dest_domain_id, owner_uid=owner_uid,
                  title=pdoc['title'], content=pdoc['content'],
                  pid=pid, hidden=hidden, category=pdoc['category'],
                  data=data, tag=pdoc.get('tag', []),
                  ac_msg=pdoc.get('ac_msg', ''))
  await document.inc(src_domain_id, document.TYPE_PROBLEM, src_pid, 'num_be_copied', 1)
  return pid


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


@argmethod.wrap
async def get_random_id(domain_id: str, **kwargs):
  pdocs = document.get_multi(domain_id=domain_id, doc_type=document.TYPE_PROBLEM, **kwargs)
  pcount = await pdocs.count()
  if pcount:
    async for pdoc in pdocs.skip(random.randrange(pcount)).limit(1):
      return pdoc['doc_id']


async def get_dict(domain_id, pids, *, fields=None, **kwargs):
  result = dict()
  async for pdoc in get_multi(domain_id=domain_id,
                              doc_id={'$in': list(set(pids))},
                              fields=fields, **kwargs):
    result[pdoc['doc_id']] = pdoc
  return result


async def get_dict_multi_domain(pdom_and_ids, *, fields=None):
  query = {'$or': []}
  key_func = lambda e: e[0]
  for domain_id, ptuples in itertools.groupby(sorted(set(pdom_and_ids), key=key_func),
                                              key=key_func):
    query['$or'].append({'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM,
                         'doc_id': {'$in': [e[1] for e in ptuples]}})
  result = dict()
  if not query['$or']:
    return result
  async for pdoc in document.get_multi(**query, fields=fields):
    result[(pdoc['domain_id'], pdoc['doc_id'])] = pdoc
  return result


@argmethod.wrap
async def get_status(domain_id: str, pid: document.convert_doc_id, uid: int, fields=None):
  return await document.get_status(domain_id, document.TYPE_PROBLEM, pid, uid, fields=fields)


@argmethod.wrap
async def inc_status(domain_id: str, pid: document.convert_doc_id, uid: int,
                     key: str, value: int):
  return await document.inc_status(domain_id, document.TYPE_PROBLEM, pid, uid, key, value)


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


def get_multi_solution_by_uid(domain_id: str, uid: int, fields=None):
  return document.get_multi(domain_id=domain_id,
                            doc_type=document.TYPE_PROBLEM_SOLUTION,
                            owner_uid=uid,
                            fields=fields)


@argmethod.wrap
async def delete_solution(domain_id: str, psid: document.convert_doc_id):
  # -num_liked
  psdoc = await get_solution(domain_id, psid)
  result = await document.delete(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
  await domain.inc_user(domain_id, psdoc['owner_uid'], num_liked=-psdoc['vote'])
  return result


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
                       .to_list()


@argmethod.wrap
async def get_solution_status(domain_id: str, psid: document.convert_doc_id, uid: int):
  return await document.get_status(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, uid)


async def get_dict_solution_status(domain_id, pids, uid, *, fields=None):
  query = {
    'domain_id': domain_id,
    'doc_type': document.TYPE_PROBLEM_SOLUTION,
    'uid': uid,
    'doc_id': {'$in': list(set(pids))},
  }
  result = dict()
  async for pssdoc in document.get_multi_status(**query, fields=fields):
    result[pssdoc['doc_id']] = pssdoc
  return result


@argmethod.wrap
async def vote_solution(domain_id: str, psid: document.convert_doc_id, uid: int, value: int):
  try:
    pssdoc = await document.capped_inc_status(domain_id, document.TYPE_PROBLEM_SOLUTION, psid,
                                              uid, 'vote', value)
  except errors.DuplicateKeyError:
    raise error.AlreadyVotedError(domain_id, psid, uid) from None
  psdoc = await document.inc(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, 'vote', value)
  await domain.inc_user(domain_id, psdoc['owner_uid'], num_liked=value)
  return psdoc, pssdoc


@argmethod.wrap
async def reply_solution(domain_id: str, psid: document.convert_doc_id, uid: int, content: str):
  validator.check_content(content)
  return await document.push(domain_id, document.TYPE_PROBLEM_SOLUTION, psid,
                             'reply', content, uid)


@argmethod.wrap
def get_solution_reply(domain_id: str, psid: document.convert_doc_id, psrid: objectid.ObjectId):
  return document.get_sub(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, 'reply', psrid)


@argmethod.wrap
def edit_solution_reply(domain_id: str, psid: document.convert_doc_id, psrid: objectid.ObjectId,
                        content: str):
  return document.set_sub(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, 'reply', psrid,
                          content=content)


@argmethod.wrap
def delete_solution_reply(domain_id: str, psid: document.convert_doc_id, psrid: objectid.ObjectId):
  return document.delete_sub(domain_id, document.TYPE_PROBLEM_SOLUTION, psid, 'reply', psrid)


async def get_data(pdoc):
  data = pdoc.get('data', None)
  if not data:
    return None
  if type(data) is dict:
    upper_pdoc = await get(data['domain'], data['pid'])
    data = upper_pdoc['data']
    if not data:
      return None
  return await fs.get_meta(data)


@argmethod.wrap
async def set_data(domain_id: str, pid: document.convert_doc_id, data: objectid.ObjectId):
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, data=data)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  await bus.publish('problem_data_change', {'domain_id': domain_id, 'pid': pid})
  return pdoc


@argmethod.wrap
async def set_hidden(domain_id: str, pid: document.convert_doc_id, hidden: bool):
  pdoc = await document.set(domain_id, document.TYPE_PROBLEM, pid, hidden=hidden)
  if not pdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM, pid)
  return pdoc


@argmethod.wrap
async def get_data_list(last: int):
  last_datetime = datetime.datetime.utcfromtimestamp(last)
  # TODO(twd2): performance improve, more elegant
  coll = db.coll('document')
  pdocs = coll.find({'doc_type': document.TYPE_PROBLEM})
  pids = []  # with domain_id
  async for pdoc in pdocs:
    data = await get_data(pdoc)
    if not data:
      continue
    date = data['uploadDate']
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
