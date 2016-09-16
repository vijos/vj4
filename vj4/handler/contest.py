import asyncio
import collections
import datetime
import pytz
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.handler import base
from vj4.util import timezone

STATUS_NEW = 0
STATUS_READY = 1
STATUS_LIVE = 2
STATUS_DONE = 3

STATUS_TEXTS = {
  STATUS_NEW: 'New',
  STATUS_READY: 'Ready (☆▽☆)',
  STATUS_LIVE: 'Live...',
  STATUS_DONE: 'Done'
}


def status_func(tdoc, now):
  now = timezone.ensure_tzinfo(now)
  begin_at = timezone.ensure_tzinfo(tdoc['begin_at'])
  end_at = timezone.ensure_tzinfo(tdoc['end_at'])
  if now < begin_at:
    if (begin_at - now).total_seconds() / 3600 <= 24:
      return STATUS_READY
    else:
      return STATUS_NEW
  elif now < end_at:
    return STATUS_LIVE
  else:
    return STATUS_DONE


@app.route('/tests', 'contest_main')
class ContestMainHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  async def get(self):
    tdocs = await contest.get_list(self.domain_id)
    tsdict = await contest.get_dict_status(self.domain_id, self.user['_id'], 
                                           [tdoc['doc_id'] for tdoc in tdocs])
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    self.render('contest_main.html', tdocs=tdocs, now=now, tsdict=tsdict)


@app.route('/tests/{tid:\w{24}}', 'contest_detail')
class ContestDetailHandler(base.OperationHandler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, tid)
    pdom_and_ids = [(tdoc['domain_id'], pid) for pid in tdoc['pids']]
    tsdoc, udoc, pdict = await asyncio.gather(contest.get_status(self.domain_id, tdoc['doc_id'],
                                                                 self.user['_id']),
                                              user.get_by_uid(tdoc['owner_uid']),
                                              problem.get_dict(pdom_and_ids))
    jdict = dict()
    rdict = dict()
    if tsdoc:
      attended = tsdoc.get('attend') == 1
      if 'journal' in tsdoc:
        for j in tsdoc['journal']:
          jdict[j['pid']] = j
        rdict = await record.get_dict([j['rid'] for j in jdict.values()])
    else:
      attended = False
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], None))
    self.render('contest_detail.html', tdoc=tdoc, tsdoc=tsdoc, attended=attended, udoc=udoc,
                pdict=pdict, jdict=jdict, rdict=rdict, now=now, page_title=tdoc['title'],
                path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_ATTEND_CONTEST)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_attend(self, *, tid: objectid.ObjectId):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    tdoc = await contest.get(self.domain_id, tid)
    if status_func(tdoc, now) == STATUS_DONE:
      raise error.ContestNotLiveError(tdoc['doc_id'])
    await contest.attend(self.domain_id, tdoc['doc_id'], self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/tests/{tid}/{pid:-?\d+|\w{24}}', 'contest_detail_problem')
class ContestDetailProblemHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    if status_func(tdoc, now) != STATUS_DONE:
      tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'],
                                       self.user['_id'])
      if not tsdoc or tsdoc.get('attend') != 1:
        raise error.ContestNotAttendedError(tdoc['doc_id'])
      if status_func(tdoc, now) != STATUS_LIVE:
        raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
      (pdoc['title'], None))
    self.render('problem_detail.html', tdoc=tdoc, pdoc=pdoc,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/tests/{tid}/{pid}/submit', 'contest_detail_problem_submit')
class ContestDetailProblemSubmitHandler(base.Handler):
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'],
                                     self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.ContestNotAttendedError(tdoc['doc_id'])
    if status_func(tdoc, now) != STATUS_LIVE:
      raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    if (contest.RULES[tdoc['rule']].show_func(tdoc, now)
        or self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
      rdocs = await record \
            .get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id']) \
            .sort([('_id', -1)]) \
            .to_list(10)
    else:
      rdocs = []
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
      (pdoc['title'], self.reverse_url('contest_detail_problem', tid=tid, pid=pid)),
      (self.translate('contest_detail_problem_submit'), None))
    self.json_or_render('problem_submit.html', tdoc=tdoc, pdoc=pdoc, rdocs=rdocs,
                        page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *,
                 tid: objectid.ObjectId, pid: document.convert_doc_id, lang: str, code: str):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid))
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'],
                                     self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.ContestNotAttendedError(tdoc['doc_id'])
    if status_func(tdoc, now) != STATUS_LIVE:
      raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION, self.user['_id'],
                           lang, code, tid=tdoc['doc_id'], hidden=True)
    await contest.update_status(self.domain_id, tdoc['_id'], self.user['_id'],
                                rid, pdoc['doc_id'], False, 0)
    if (not contest.RULES[tdoc['rule']].show_func(tdoc, now)
        and not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
        self.json_or_redirect(self.reverse_url('contest_detail', tid=tdoc['_id']))
    else:
      self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/tests/{tid}/status', 'contest_status')
class ContestStatusHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST_STATUS)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, tid)
    # TODO(iceboy): This does not work on multi-machine environment.
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    if (not contest.RULES[tdoc['rule']].show_func(tdoc, now)
        and not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
      raise error.ContestStatusHiddenError()
    pdom_and_ids = [(tdoc['domain_id'], pid) for pid in tdoc['pids']]
    udict, pdict = await asyncio.gather(user.get_dict([tsdoc['uid'] for tsdoc in tsdocs]),
                                        problem.get_dict(pdom_and_ids))
    tspdict = {}
    for tsdoc in tsdocs:
      pdict = {}
      for pdetail in tsdoc.get('detail', []):
        pdict[pdetail['pid']] = pdetail
      tspdict[tsdoc['uid']] = pdict
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], self.reverse_url('contest_detail', tid=tdoc['doc_id'])),
      (self.translate('contest_status'), None))
    self.render('contest_status.html', tdoc=tdoc, tsdocs=tsdocs,
                pdict=pdict, udict=udict, tspdict=tspdict,
                path_components=path_components)


@app.route('/tests/create', 'contest_create')
class ContestCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  async def get(self):
    tz = pytz.timezone(self.timezone)
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    dt = now.astimezone(tz)
    ts = int(dt.timestamp())
    # find next quarter
    ts = ts - ts % (15 * 60) + 15 * 60
    dt = datetime.datetime.fromtimestamp(ts, tz)
    self.render('contest_create.html',
                date_text=dt.strftime('%Y-%m-%d'),
                time_text=dt.strftime('%H:%M'))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, title: str, content: str, rule: int,
                 begin_at_date: str,
                 begin_at_time: str,
                 duration: float,
                 pids: str):
    try:
      tz = pytz.timezone(self.timezone)
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = tz.localize(begin_at)
      end_at = tz.normalize(begin_at + datetime.timedelta(hours=duration))
    except ValueError as e:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    if begin_at <= now:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    if begin_at >= end_at:
      raise error.ValidationError('duration')
    pids = list(set(map(document.convert_doc_id, pids.split(','))))
    pdocs = (await problem.get_multi(domain_id=self.domain_id, fields={'doc_id': 1}, doc_id={'$in': pids})
             .sort('doc_id', 1)
             .to_list(None))
    exist_pids = [pdoc['doc_id'] for pdoc in pdocs]
    if len(pids) != len(exist_pids):
      for pid in pids:
        if pid not in exist_pids:
          raise error.ProblemNotFoundError(self.domain_id, pid)
    tid = await contest.add(self.domain_id, title, content, self.user['_id'],
                            rule, begin_at, end_at, pids)
    for pid in pids:
      await problem.set_hidden(self.domain_id, pid, True)
    self.json_or_redirect(self.reverse_url('contest_detail', tid=tid))
