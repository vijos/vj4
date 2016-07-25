import datetime

from bson import objectid

from vj4 import db
from vj4 import constant
from vj4.model import document
from vj4.util import argmethod

@argmethod.wrap
async def add(domain_id: str, pid: document.convert_doc_id, type: int, uid: int,
              lang: str, code: str, data_id: objectid.ObjectId=None, tid: objectid.ObjectId=None,
              hidden=False):
  coll = db.Collection('record')
  return await coll.insert({'hidden': hidden,
                            'status': constant.record.STATUS_WAITING,
                            'score': 0,
                            'time_ms': 0,
                            'memory_kb': 0,
                            'domain_id': domain_id,
                            'pid': pid,
                            'uid': uid,
                            'lang': lang,
                            'code': code,
                            'tid': tid,
                            'data_id': data_id,
                            'type': type})

@argmethod.wrap
async def get(record_id: objectid.ObjectId):
  coll = db.Collection('record')
  return await coll.find_one(record_id)


@argmethod.wrap
def get_all_multi(end_id: objectid.ObjectId = None, *, fields=None):
  coll = db.Collection('record')
  query = {'hidden': False}
  if end_id:
    query['_id'] = {'$lt': end_id}
  return coll.find(query, fields=fields)


@argmethod.wrap
def get_user_in_problem_multi(uid: int, domain_id: str, pid: document.convert_doc_id, *, fields=None):
  coll = db.Collection('record')
  query = {'hidden': False, 'domain_id': domain_id, 'pid': pid, 'uid': uid}
  return coll.find(query, fields=fields)


@argmethod.wrap
async def begin_judge(record_id: objectid.ObjectId,
                      judge_uid: int, judge_token: str, status: int):
  coll = db.Collection('record')
  doc = await coll.find_and_modify(query={'_id': record_id},
                                   update={'$set': {'status': status,
                                                    'judge_uid': judge_uid,
                                                    'judge_token': judge_token,
                                                    'judge_at': datetime.datetime.utcnow(),
                                                    'compiler_texts': [],
                                                    'judge_texts': [],
                                                    'cases': []}},
                                   new=True)
  return doc


async def next_judge(record_id, judge_uid, judge_token, **kwargs):
  coll = db.Collection('record')
  doc = await coll.find_and_modify(query={'_id': record_id,
                                          'judge_uid': judge_uid,
                                          'judge_token': judge_token},
                                   update=kwargs,
                                   new=True)
  return doc


@argmethod.wrap
async def end_judge(record_id: objectid.ObjectId, judge_uid: int, judge_token: str,
                    status: int, score: int, time_ms: int, memory_kb: int):
  coll = db.Collection('record')
  doc = await coll.find_and_modify(query={'_id': record_id,
                                          'judge_uid': judge_uid,
                                          'judge_token': judge_token},
                                   update={'$set': {'status': status,
                                                    'score': score,
                                                    'time_ms': time_ms,
                                                    'memory_kb': memory_kb},
                                           '$unset': {'judge_token': ''}},
                                   new=True)
  return doc


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('record')
  await coll.ensure_index([('hidden', 1),
                           ('_id', -1)])
  await coll.ensure_index([('hidden', 1),
                           ('domain_id', 1),
                           ('pid', 1),
                           ('uid', 1),
                           ('_id', -1)])
  # TODO(iceboy): Add more indexes.


if __name__ == '__main__':
  argmethod.invoke_by_args()
