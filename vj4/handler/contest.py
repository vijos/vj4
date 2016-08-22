import asyncio
import collections
import datetime
import pytz
from bson import objectid

from vj4 import app
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import record
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.handler import base

STATUS_TEXTS = {
  contest.STATUS_NEW: 'New',
  contest.STATUS_READY: 'Ready',
  contest.STATUS_LIVE: 'Live',
  contest.STATUS_DONE: 'Done'
}

TYPE_TEXTS = collections.OrderedDict([
  (contest.RULE_OI, 'OI'),
  (contest.RULE_ACM, 'ACM/ICPC')
])


@app.route('/tests', 'contest_main')
class ContestMainHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  async def get(self):
    tdocs = await contest.get_list(self.domain_id)
    self.render('contest_main.html', tdocs=tdocs)


@app.route('/tests/{tid:\w{24}}', 'contest_detail')
class ContestDetailHandler(base.OperationHandler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, tid)
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'],
                                     {'attend': 1})
    if tsdoc:
      attended = tsdoc.get('attend') == 1
    else:
      attended = False
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], None))
    self.render('contest_detail.html', tdoc=tdoc, attended=attended,
                path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_ATTEND_CONTEST)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_attend(self, *, tid: objectid.ObjectId):
    await contest.attend(self.domain_id, tid, self.user['_id'])
    self.json_or_redirect(self.reverse_url('contest_detail', tid=tid))


# TODO(twd2): combine with problem submit?
@app.route('/tests/{tid}/{pid:-?\d+|\w{24}}', 'contest_detail_problem')
class ContestDetailProblemHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    # TODO(iceboy): Check if the user attended the contest.
    # TODO(iceboy): Check if the problem belongs to the contest.
    # TODO(iceboy): Check if contest can be viewed.
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
      (pdoc['title'], None))
    self.render('problem_detail.html', tdoc=tdoc, pdoc=pdoc,
                page_title=pdoc['title'], path_components=path_components)


# TODO(twd2): combine with problem submit?
@app.route('/tests/{tid}/{pid}/submit', 'contest_detail_problem_submit')
class ContestDetailProblemSubmitHandler(base.Handler):
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    # TODO(iceboy): Check if the user attended the contest.
    # TODO(iceboy): Check if the problem belongs to the contest.
    # TODO(iceboy): Check if contest can be submitted.
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
      (pdoc['title'], self.reverse_url('contest_detail_problem', tid=tid, pid=pid)),
      ('contest_detail_problem_submit', None))
    self.json_or_render('problem_submit.html', tdoc=tdoc, pdoc=pdoc,
                        page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *,
                 tid: objectid.ObjectId, pid: document.convert_doc_id, lang: str, code: str):
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid))
    # TODO(iceboy): Check if the user attended the contest.
    # TODO(iceboy): Check if the problem belongs to the contest.
    # TODO(iceboy): Check if contest can be submitted.
    rid = await record.add(self.domain_id, pdoc['doc_id'], record.TYPE_SUBMISSION, self.user['_id'],
                           lang, code, tid=tdoc['doc_id'], hidden=True)
    self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/tests/{tid}/status', 'contest_status')
class ContestStatusHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST_STATUS)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, tid)
    # TODO(iceboy): This does not work on multi-machine environment.
    if (not contest.RULES[tdoc['rule']].show_func(tdoc, self.now)
        and not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
      raise error.ContestStatusHiddenError()
    path_components = self.build_path(
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], self.reverse_url('contest_detail', tid=tdoc['doc_id'])),
      (self.translate('contest_status'), None))
    self.render('contest_status.html', tdoc=tdoc, tsdocs=tsdocs, path_components=path_components)


@app.route('/tests/create', 'contest_create')
class ContestCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  async def get(self):
    tz = pytz.timezone(self.timezone)
    dt = self.now.astimezone(tz)
    ts = int(dt.timestamp())
    # find next quarter
    ts = ts - ts % (15 * 60) + 15 * 60
    dt = datetime.datetime.fromtimestamp(ts, tz)
    self.render('contest_create.html',
                date_text=dt.strftime('%Y-%m-%d'),
                time_text=dt.strftime('%H:%M'))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
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
    if begin_at <= self.now:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    if begin_at >= end_at:
      raise error.ValidationError('duration')
    pids = list(set(map(document.convert_doc_id, pids.split(','))))
    pdocs = (await problem.get_multi(self.domain_id, fields={'doc_id': 1}, doc_id={'$in': pids})
             .sort('doc_id', 1)
             .to_list(None))
    exist_pids = [pdoc['doc_id'] for pdoc in pdocs]
    if len(pids) != len(exist_pids):
      for pid in pids:
        if pid not in exist_pids:
          raise error.ProblemNotFoundError(self.domain_id, pid)
    tid = await contest.add(self.domain_id, title, content, self.user['_id'],
                            rule, begin_at, end_at, pids)
    # TODO(twd2): set problem properties e.g. hidden, ...
    self.json_or_redirect(self.reverse_url('contest_detail', tid=tid))
