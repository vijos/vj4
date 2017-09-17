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


journal_key_func = lambda j: j['rid']

Rule = collections.namedtuple('Rule', ['show_func', 'stat_func', 'status_sort', 'rank_func',
                                       'scoreboard_func'])


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


def _oi_scoreboard(is_export, _, tdoc, ranked_tsdocs, udict, pdict):
  columns = []
  columns.append({'type': 'rank', 'value': _('Rank')})
  columns.append({'type': 'user', 'value': _('User')})
  columns.append({'type': 'total_score', 'value': _('Total Score')})
  for index, pid in enumerate(tdoc['pids']):
    if is_export:
      columns.append({'type': 'problem_score', 
                      'value': '#{0} {1}'.format(index + 1, pdict[pid]['title'])})
    else:
      columns.append({'type': 'problem_detail',
                      'value': '#{0}'.format(index + 1), 'raw': pdict[pid]})
  rows = [columns]
  for rank, tsdoc in ranked_tsdocs:
    if 'detail' in tsdoc:
      tsddict = {item['pid']: item for item in tsdoc['detail']}
    else:
      tsddict = {}
    row = []
    row.append({'type': 'string', 'value': rank})
    row.append({'type': 'user', 
                'value': udict[tsdoc['uid']]['uname'], 'raw': udict[tsdoc['uid']]})
    row.append({'type': 'string', 'value': tsdoc.get('score', 0)})
    for pid in tdoc['pids']:
      row.append({'type': 'record',
                  'value': tsddict.get(pid, {}).get('score', '-'),
                  'raw': tsddict.get(pid, {}).get('rid', None)})
    rows.append(row)
  return rows


def _acm_scoreboard(is_export, _, tdoc, ranked_tsdocs, udict, pdict):
  columns = []
  columns.append({'type': 'rank', 'value': _('Rank')})
  columns.append({'type': 'user', 'value': _('User')})
  columns.append({'type': 'solved_problems', 'value': _('Solved Problems')})
  if is_export: columns.append({'type': 'total_time',
                                'value': _('Total Time')})
  for index, pid in enumerate(tdoc['pids']):
    if is_export:
      columns.append({'type': 'problem_flag',
                      'value': '#{0} {1}'.format(index + 1, pdict[pid]['title'])})
      columns.append({'type': 'problem_time',
                      'value': '#{0} {1}'.format(index + 1, _('Time'))})
    else:
      columns.append({'type': 'problem_detail',
                      'value': '#{0}'.format(index + 1), 'raw': pdict[pid]})
  rows = [columns]
  for rank, tsdoc in ranked_tsdocs:
    if 'detail' in tsdoc:
      tsddict = {item['pid']: item for item in tsdoc['detail']}
    else:
      tsddict = {}
    row = []
    row.append({'type': 'string', 'value': rank})
    row.append({'type': 'user',
                'value': udict[tsdoc['uid']]['uname'], 'raw': udict[tsdoc['uid']]})
    row.append({'type': 'string',
                'value': tsdoc.get('accept', 0)})
    if is_export: row.append({'type': 'string', 'value': tsdoc.get('time', 0.0)})
    for pid in tdoc['pids']:
      if tsddict.get(pid, {}).get('accept', False):
        rdoc = tsddict[pid]['rid']
        col_accepted = _('Accepted')
        col_time = tsddict[pid]['time']
      else:
        rdoc = None
        col_accepted = '-'
        col_time = '-'
      if is_export:
        row.append({'type': 'string', 'value': col_accepted})
        row.append({'type': 'string', 'value': col_time})
      else:
        row.append({'type': 'record',
                    'value': '{0}\n{1}'.format(col_accepted, col_time), 'raw': rdoc})
    rows.append(row)
  return rows


RULES = {
  constant.contest.RULE_OI: Rule(lambda tdoc, now: now > tdoc['end_at'],
                                 _oi_stat,
                                 [('score', -1)],
                                 functools.partial(rank.ranked, equ_func=_oi_equ_func),
                                 _oi_scoreboard),
  constant.contest.RULE_ACM: Rule(lambda tdoc, now: now >= tdoc['begin_at'],
                                  _acm_stat,
                                  [('accept', -1), ('time', 1)],
                                  functools.partial(enumerate, start=1),
                                  _acm_scoreboard),
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


async def edit(domain_id: str, tid: objectid.ObjectId, **kwargs):
  if 'title' in kwargs:
      validator.check_title(kwargs['title'])
  if 'content' in kwargs:
      validator.check_content(kwargs['content'])
  if 'rule' in kwargs:
    if kwargs['rule'] not in RULES:
      raise error.ValidationError('rule')
  if 'begin_at' in kwargs and 'end_at' in kwargs:
    if kwargs['begin_at'] >= kwargs['end_at']:
      raise error.ValidationError('begin_at', 'end_at')
  return await document.set(domain_id, document.TYPE_CONTEST, tid, **kwargs)


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
                         .to_list()
  return tdoc, tsdocs


def _get_status_journal(tsdoc):
  # Sort and uniquify journal of the contest status document, by rid.
  return [list(g)[-1]
             for _, g in itertools.groupby(sorted(tsdoc['journal'], key=journal_key_func), key=journal_key_func)]


@argmethod.wrap
async def update_status(domain_id: str, tid: objectid.ObjectId, uid: int, rid: objectid.ObjectId,
                        pid: document.convert_doc_id, accept: bool, score: int):
  """This method returns None when the modification has been superseded by a parallel operation."""
  tdoc = await document.get(domain_id, document.TYPE_CONTEST, tid)
  tsdoc = await document.rev_push_status(
    domain_id, document.TYPE_CONTEST, tdoc['doc_id'], uid,
    'journal', {'rid': rid, 'pid': pid, 'accept': accept, 'score': score})
  if 'attend' not in tsdoc or not tsdoc['attend']:
    raise error.ContestNotAttendedError(domain_id, tid, uid)

  journal = _get_status_journal(tsdoc)
  stats = RULES[tdoc['rule']].stat_func(tdoc, journal)
  tsdoc = await document.rev_set_status(domain_id, document.TYPE_CONTEST, tid, uid, tsdoc['rev'],
                                        journal=journal, **stats)
  return tsdoc


@argmethod.wrap
async def recalc_status(domain_id: str, tid: objectid.ObjectId):
  tdoc = await document.get(domain_id, document.TYPE_CONTEST, tid)
  async with document.get_multi_status(domain_id=domain_id,
                                       doc_type=document.TYPE_CONTEST,
                                       doc_id=tdoc['doc_id']) as tsdocs:
    async for tsdoc in tsdocs:
      if 'attend' not in tsdoc or not tsdoc['attend']:
        continue
      journal = _get_status_journal(tsdoc)
      stats = RULES[tdoc['rule']].stat_func(tdoc, journal)
      await document.rev_set_status(domain_id, document.TYPE_CONTEST, tid, tsdoc['uid'],
                                    tsdoc['rev'], return_doc=False, journal=journal, **stats)


if __name__ == '__main__':
  argmethod.invoke_by_args()
