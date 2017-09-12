import asyncio
import collections
import datetime
import pytz
import yaml
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import opcount
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.handler import base
from vj4.handler import contest as contestHandler
from vj4.handler import problem as problemHandler
from vj4.util import pagination


def _parse_penalty_rules_yaml(penalty_rules):
  try:
    penalty_rules = yaml.safe_load(penalty_rules)
  except yaml.YAMLError:
    raise error.ValidationError('penalty_rules', 'parse error')
  if not isinstance(penalty_rules, dict):
    raise error.ValidationError('penalty_rules', 'invalid format')
  new_rules = collections.OrderedDict()
  try:
    for time, coefficient in sorted(penalty_rules.items(), key=lambda x: float(x[0])):
      time_val = str(int(float(time) * 60 * 60))
      coefficient_val = float(coefficient)
      new_rules[time_val] = coefficient_val
  except ValueError:
    raise error.ValidationError('penalty_rules', 'value error')
  return new_rules


def _format_penalty_rules_yaml(penalty_rules):
  # yaml does not support dump from ordereddict so that we output yaml document manually here
  yaml_doc = ''
  for time, coefficient in sorted(penalty_rules.items(), key=lambda x: int(x[0])):
    time_val = round(float(time) / 60 / 60, ndigits=2)
    yaml_doc += '{0}: {1}\n'.format(time_val, coefficient)
  return yaml_doc


class HomeworkStatusMixin(contestHandler.ContestStatusMixin):
  def is_ready(self, tdoc):
    return self.now < tdoc['begin_at']

  def is_live(self, tdoc):
    return tdoc['begin_at'] <= self.now < tdoc['penalty_since']

  def is_extend(self, tdoc):
    return tdoc['penalty_since'] <= self.now < tdoc['end_at']

  def is_done(self, tdoc):
    return self.now >= tdoc['end_at']

  def get_status(self, tdoc):
    if self.is_ready(tdoc):
      return 'ready'
    if self.is_live(tdoc):
      return 'live'
    elif self.is_extend(tdoc):
      return 'extend'
    else:
      return 'done'


@app.route('/homework', 'homework_main')
class HomeworkMainHandler(base.Handler, HomeworkStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.get_argument
  @base.sanitize
  async def get(self):
    tdocs = await contest.get_multi(self.domain_id, rule={'$in': constant.contest.HOMEWORK_RULES}).to_list()
    calendar_tdocs = []
    for tdoc in tdocs:
      cal_tdoc = {'_id': tdoc['_id'],
                  'begin_at': self.datetime_stamp(tdoc['begin_at']),
                  'title': tdoc['title'],
                  'status': self.get_status(tdoc),
                  'url': self.reverse_url('homework_detail', tid=tdoc['doc_id'])}
      if cal_tdoc['status'] == 'extend' or cal_tdoc['status'] == 'done':
        cal_tdoc['end_at'] = self.datetime_stamp(tdoc['end_at'])
        cal_tdoc['penalty_since'] = self.datetime_stamp(tdoc['penalty_since'])
      else:
        cal_tdoc['end_at'] = self.datetime_stamp(tdoc['penalty_since'])
      calendar_tdocs.append(cal_tdoc)
    self.render('homework_main.html', tdocs=tdocs, calendar_tdocs=calendar_tdocs)


@app.route('/homework/{tid:\w{24}}', 'homework_detail')
class HomeworkDetailHandler(base.OperationHandler, HomeworkStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    # homework
    tdoc = await contest.get_homework(self.domain_id, tid)
    tsdoc, pdict = await asyncio.gather(
        contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        problem.get_dict(self.domain_id, tdoc['pids']))
    psdict = dict()
    rdict = dict()
    if tsdoc:
      attended = tsdoc.get('attend') == 1
      for pdetail in tsdoc.get('detail', []):
        psdict[pdetail['pid']] = pdetail
      if self.can_show(tdoc):
        rdict = await record.get_dict((psdoc['rid'] for psdoc in psdict.values()),
                                      get_hidden=True)
      else:
        rdict = dict((psdoc['rid'], {'_id': psdoc['rid']}) for psdoc in psdict.values())
    else:
      attended = False
    path_components = self.build_path(
        (self.translate('homework_main'), self.reverse_url('homework_main')),
        (tdoc['title'], None))
    self.render('homework_detail.html', tdoc=tdoc, tsdoc=tsdoc, attended=attended,
                pdict=pdict, psdict=psdict, rdict=rdict,
                page_title=tdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_ATTEND_HOMEWORK)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_attend(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get_homework(self.domain_id, tid)
    if self.is_done(tdoc):
      raise error.HomeworkNotLiveError(tdoc['doc_id'])
    await contest.attend(self.domain_id, tdoc['doc_id'], self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/homework/{tid}/{pid:-?\d+|\w{24}}', 'homework_detail_problem')
class HomeworkDetailProblemHandler(base.Handler, HomeworkStatusMixin, problemHandler.ProblemMixin):
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get_homework(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    if not self.is_done(tdoc):
      tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
      if not tsdoc or tsdoc.get('attend') != 1:
        raise error.HomeworkNotAttendedError(tdoc['doc_id'])
      if self.is_ready(tdoc):
        raise error.HomeworkNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    tsdoc, udoc = await asyncio.gather(
        contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    path_components = self.build_path(
        (self.translate('homework_main'), self.reverse_url('homework_main')),
        (tdoc['title'], self.reverse_url('homework_detail', tid=tid)),
        (pdoc['title'], None))
    self.render('problem_detail.html', tdoc=tdoc, pdoc=pdoc, tsdoc=tsdoc, udoc=udoc,
                attended=attended,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/homework/{tid}/{pid}/submit', 'homework_detail_problem_submit')
class HomeworkDetailProblemSubmitHandler(base.Handler, HomeworkStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get_homework(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.HomeworkNotAttendedError(tdoc['doc_id'])
    if self.is_ready(tdoc):
      raise error.HomeworkNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    tsdoc, udoc = await asyncio.gather(
        contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    if contest.RULES[tdoc['rule']].show_func(tdoc, self.now):
      rdocs = await record.get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id']) \
                          .sort([('_id', -1)]) \
                          .limit(10) \
                          .to_list()
    else:
      rdocs = []
    if not self.prefer_json:
      path_components = self.build_path(
          (self.translate('homework_main'), self.reverse_url('homework_main')),
          (tdoc['title'], self.reverse_url('homework_detail', tid=tid)),
          (pdoc['title'], self.reverse_url('homework_detail_problem', tid=tid, pid=pid)),
          (self.translate('homework_detail_problem_submit'), None))
      self.render('problem_submit.html', tdoc=tdoc, pdoc=pdoc, rdocs=rdocs,
                  tsdoc=tsdoc, udoc=udoc, attended=attended,
                  page_title=pdoc['title'], path_components=path_components)
    else:
      self.json({'rdocs': rdocs})

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *,
                 tid: objectid.ObjectId, pid: document.convert_doc_id, lang: str, code: str):
    await opcount.inc(**opcount.OPS['run_code'], ident=opcount.PREFIX_USER + str(self.user['_id']))
    tdoc, pdoc = await asyncio.gather(contest.get_homework(self.domain_id, tid),
                                      problem.get(self.domain_id, pid))
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.HomeworkNotAttendedError(tdoc['doc_id'])
    if self.is_ready(tdoc):
      raise error.HomeworkNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION,
                           self.user['_id'], lang, code, tid=tdoc['doc_id'], hidden=True)
    await contest.update_status(self.domain_id, tdoc['doc_id'], self.user['_id'],
                                rid, pdoc['doc_id'], False, 0)
    if not contest.RULES[tdoc['rule']].show_func(tdoc, self.now):
        self.json_or_redirect(self.reverse_url('homework_detail', tid=tdoc['doc_id']))
    else:
      self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/homework/create', 'homework_create')
class HomeworkCreateHandler(base.Handler, HomeworkStatusMixin):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_HOMEWORK)
  async def get(self):
    begin_at = self.now.replace(tzinfo=pytz.utc).astimezone(self.timezone) + datetime.timedelta(days=1)
    penalty_since = begin_at + datetime.timedelta(days=7)
    self.render('homework_edit.html',
                date_begin_text=begin_at.strftime('%Y-%m-%d'),
                time_begin_text='00:00',
                date_penalty_text=penalty_since.strftime('%Y-%m-%d'),
                time_penalty_text='23:59',
                extension_days='1')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.require_perm(builtin.PERM_CREATE_HOMEWORK)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, title: str, content: str,
                 begin_at_date: str, begin_at_time: str,
                 penalty_since_date: str, penalty_since_time: str,
                 extension_days: float, penalty_rules: str,
                 pids: str):
    penalty_rules = _parse_penalty_rules_yaml(penalty_rules)
    try:
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = self.timezone.localize(begin_at).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError as e:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    try:
      penalty_since = datetime.datetime.strptime(penalty_since_date + ' ' + penalty_since_time, '%Y-%m-%d %H:%M')
      penalty_since = self.timezone.localize(penalty_since).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError as e:
      raise error.ValidationError('end_at_date', 'end_at_time')
    end_at = penalty_since + datetime.timedelta(days=extension_days)
    if begin_at <= self.now:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    if begin_at >= penalty_since:
      raise error.ValidationError('end_at_date', 'end_at_time')
    if penalty_since > end_at:
      raise error.ValidationError('extension_days')
    pids = list(set(map(document.convert_doc_id, pids.split(','))))
    pdocs = await problem.get_multi(domain_id=self.domain_id, doc_id={'$in': pids},
                                    fields={'doc_id': 1}) \
                         .sort('doc_id', 1) \
                         .to_list()
    exist_pids = [pdoc['doc_id'] for pdoc in pdocs]
    if len(pids) != len(exist_pids):
      for pid in pids:
        if pid not in exist_pids:
          raise error.ProblemNotFoundError(self.domain_id, pid)
    tid = await contest.add(self.domain_id, title, content, self.user['_id'],
                            constant.contest.RULE_ASSIGNMENT, begin_at, end_at, pids,
                            penalty_since=penalty_since, penalty_rules=penalty_rules)
    for pid in pids:
      await problem.set_hidden(self.domain_id, pid, True)
    self.json_or_redirect(self.reverse_url('homework_detail', tid=tid))


@app.route('/homework/{tid}/edit', 'homework_edit')
class HomeworkEditHandler(base.Handler, HomeworkStatusMixin):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get_homework(self.domain_id, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_HOMEWORK_SELF):
      self.check_perm(builtin.PERM_EDIT_HOMEWORK)
    begin_at = pytz.utc.localize(tdoc['begin_at']).astimezone(self.timezone)
    penalty_since = pytz.utc.localize(tdoc['penalty_since']).astimezone(self.timezone)
    end_at = pytz.utc.localize(tdoc['end_at']).astimezone(self.timezone)
    extension_days = round((end_at - penalty_since).total_seconds() / 60 / 60 / 24, ndigits=2)
    self.render('homework_edit.html', tdoc=tdoc,
                date_begin_text=begin_at.strftime('%Y-%m-%d'),
                time_begin_text=begin_at.strftime('%H:%M'),
                date_penalty_text=penalty_since.strftime('%Y-%m-%d'),
                time_penalty_text=penalty_since.strftime('%H:%M'),
                extension_days=extension_days,
                penalty_rules=_format_penalty_rules_yaml(tdoc['penalty_rules']))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, tid: objectid.ObjectId, title: str, content: str,
                 begin_at_date: str, begin_at_time: str,
                 penalty_since_date: str, penalty_since_time: str,
                 extension_days: float, penalty_rules: str,
                 pids: str):
    tdoc = await contest.get_homework(self.domain_id, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_HOMEWORK_SELF):
      self.check_perm(builtin.PERM_EDIT_HOMEWORK)
    penalty_rules = _parse_penalty_rules_yaml(penalty_rules)
    try:
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = self.timezone.localize(begin_at).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError as e:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    try:
      penalty_since = datetime.datetime.strptime(penalty_since_date + ' ' + penalty_since_time, '%Y-%m-%d %H:%M')
      penalty_since = self.timezone.localize(penalty_since).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError as e:
      raise error.ValidationError('end_at_date', 'end_at_time')
    end_at = penalty_since + datetime.timedelta(days=extension_days)
    if begin_at <= self.now:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    if begin_at >= penalty_since:
      raise error.ValidationError('end_at_date', 'end_at_time')
    if penalty_since > end_at:
      raise error.ValidationError('extension_days')
    pids = list(set(map(document.convert_doc_id, pids.split(','))))
    pdocs = await problem.get_multi(domain_id=self.domain_id, doc_id={'$in': pids},
                                    fields={'doc_id': 1}) \
                         .sort('doc_id', 1) \
                         .to_list()
    exist_pids = [pdoc['doc_id'] for pdoc in pdocs]
    if len(pids) != len(exist_pids):
      for pid in pids:
        if pid not in exist_pids:
          raise error.ProblemNotFoundError(self.domain_id, pid)
    await contest.edit(self.domain_id, tdoc['doc_id'], title=title, content=content,
                       begin_at=begin_at, end_at=end_at, pids=pids,
                       penalty_since=penalty_since, penalty_rules=penalty_rules)
    await contest.recalc_contest_status(self.domain_id, tdoc['doc_id'])
    for pid in pids:
      await problem.set_hidden(self.domain_id, pid, True)
    self.json_or_redirect(self.reverse_url('homework_detail', tid=tid))
