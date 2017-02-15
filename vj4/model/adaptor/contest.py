import collections
import datetime
import functools
import itertools

from bson import objectid
from pymongo import errors

from vj4 import constant
from vj4 import error
from vj4.model import document
from vj4.util import argmethod
from vj4.util import validator
from vj4.util import rank


Rule = collections.namedtuple('Rule', ['show_func', 'stat_func', 'status_sort', 'rank_func'])


def _oi_stat(tdoc, journal):
  detail = list(dict((j['pid'], j) for j in journal if j['pid'] in tdoc['pids']).values())
  return {'score': sum(d['score'] for d in detail), 'detail': detail}


def _acm_stat(tdoc, journal):
  naccept = collections.defaultdict(int)
  effective = {}
  for j in journal:
    if j['pid'] in tdoc['pids'] and not (j['pid'] in effective and effective[j['pid']]['accept']):
      effective[j['pid']] = j
      if not j['accept']:
        naccept[j['pid']] += 1

  def time(jdoc):
    real = jdoc['rid'].generation_time.replace(tzinfo=None) - tdoc['begin_at']
    penalty = datetime.timedelta(minutes=20) * naccept[jdoc['pid']]
    return (real + penalty).total_seconds()

  detail = [{**j, 'naccept': naccept[j['pid']], 'time': time(j)} for j in effective.values()]
  return {'accept': sum(int(d['accept']) for d in detail),
          'time': sum(d['time'] for d in detail if d['accept']),
          'detail': detail}


def _oi_equ_func(a, b):
  return a.get('score', 0) == b.get('score', 0)

RULES = {
  constant.contest.RULE_OI: Rule(lambda tdoc, now: now > tdoc['end_at'], _oi_stat, [('score', -1)],
                                 functools.partial(rank.ranked, equ_func=_oi_equ_func)),
  constant.contest.RULE_ACM: Rule(lambda tdoc, now: now >= tdoc['begin_at'], _acm_stat,
                                  [('accept', -1), ('time', 1)], functools.partial(enumerate,
                                                                                   start=1)),
}


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int, rule: int,
              begin_at: lambda i: datetime.datetime.utcfromtimestamp(int(i)),
              end_at: lambda i: datetime.datetime.utcfromtimestamp(int(i)),
              pids=[]):
  validator.check_title(title)
  validator.check_content(content)
  if rule not in RULES:
    raise error.ValidationError('rule')
  if begin_at >= end_at:
    raise error.ValidationError('begin_at', 'end_at')
  # TODO(twd2): should we check problem existance here?
  return await document.add(domain_id, content, owner_uid, document.TYPE_CONTEST,
                            title=title, rule=rule,
                            begin_at=begin_at, end_at=end_at, pids=pids, attend=0)


@argmethod.wrap
async def get(domain_id: str, tid: objectid.ObjectId):
  tdoc = await document.get(domain_id, document.TYPE_CONTEST, tid)
  if not tdoc:
    raise error.DocumentNotFoundError(domain_id, document.TYPE_CONTEST, tid)
  return tdoc


def get_multi(domain_id: str, fields=None, **kwargs):
  # TODO(twd2): projection.
  return document.get_multi(domain_id=domain_id,
                            doc_type=document.TYPE_CONTEST,
                            fields=fields,
                            **kwargs) \
                 .sort([('doc_id', -1)])


@argmethod.wrap
async def attend(domain_id: str, tid: objectid.ObjectId, uid: int):
  # TODO(iceboy): check time.
  try:
    await document.capped_inc_status(domain_id, document.TYPE_CONTEST, tid,
                                     uid, 'attend', 1, 0, 1)
  except errors.DuplicateKeyError:
    raise error.ContestAlreadyAttendedError(domain_id, tid, uid) from None
  return await document.inc(domain_id, document.TYPE_CONTEST, tid, 'attend', 1)


@argmethod.wrap
async def get_status(domain_id: str, tid: objectid.ObjectId, uid: int, fields=None):
  return await document.get_status(domain_id, document.TYPE_CONTEST, doc_id=tid,
                                   uid=uid, fields=fields)


def get_multi_status(*, fields=None, **kwargs):
  return document.get_multi_status(doc_type=document.TYPE_CONTEST, fields=fields, **kwargs)


async def get_dict_status(domain_id, uid, tids, *, fields=None):
  result = dict()
  async for tsdoc in get_multi_status(domain_id=domain_id,
                                      uid=uid,
                                      doc_id={'$in': list(set(tids))},
                                      fields=fields):
    result[tsdoc['doc_id']] = tsdoc
  return result


@argmethod.wrap
async def get_and_list_status(domain_id: str, tid: objectid.ObjectId, fields=None):
  # TODO(iceboy): projection, pagination.
  tdoc = await get(domain_id, tid)
  tsdocs = await document.get_multi_status(domain_id=domain_id,
                                           doc_type=document.TYPE_CONTEST,
                                           doc_id=tdoc['doc_id'],
                                           fields=fields) \
                         .sort(RULES[tdoc['rule']].status_sort) \
                         .to_list(None)
  return tdoc, tsdocs


@argmethod.wrap
async def update_status(domain_id: str, tid: objectid.ObjectId, uid: int, rid: objectid.ObjectId,
                        pid: document.convert_doc_id, accept: bool, score: int):
  """This method returns None when the modification has been superseded by a parallel operation."""
  tdoc = await document.get(domain_id, document.TYPE_CONTEST, tid)
  if pid not in tdoc['pids']:
    raise error.ValidationError('pid')

  tsdoc = await document.rev_push_status(
    domain_id, document.TYPE_CONTEST, tdoc['doc_id'], uid,
    'journal', {'rid': rid, 'pid': pid, 'accept': accept, 'score': score})
  if 'attend' not in tsdoc or not tsdoc['attend']:
    raise error.ContestNotAttendedError(domain_id, tid, uid)

  # Sort and uniquify journal of the contest status document, by rid.
  key_func = lambda j: j['rid']
  journal = [list(g)[-1]
             for _, g in itertools.groupby(sorted(tsdoc['journal'], key=key_func), key=key_func)]
  stats = RULES[tdoc['rule']].stat_func(tdoc, journal)
  tsdoc = await document.rev_set_status(domain_id, document.TYPE_CONTEST, tid, uid, tsdoc['rev'],
                                        journal=journal, **stats)
  return tsdoc


if __name__ == '__main__':
  argmethod.invoke_by_args()
