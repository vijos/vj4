import asyncio
import calendar
import collections
import datetime
import functools
import io
import pytz
import yaml
import zipfile
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import record
from vj4.model import user
from vj4.model import domain
from vj4.model.adaptor import discussion
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.handler import base
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


@app.route('/homework', 'homework_main')
class HomeworkMainHandler(contest.ContestMixin, base.Handler):
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  async def get(self):
    tdocs = await contest.get_multi(self.domain_id, document.TYPE_HOMEWORK).to_list()
    calendar_tdocs = []
    for tdoc in tdocs:
      cal_tdoc = {'id': tdoc['doc_id'],
                  'begin_at': self.datetime_stamp(tdoc['begin_at']),
                  'title': tdoc['title'],
                  'status': self.status_text(tdoc),
                  'url': self.reverse_url('homework_detail', tid=tdoc['doc_id'])}
      if self.is_homework_extended(tdoc) or self.is_done(tdoc):
        cal_tdoc['end_at'] = self.datetime_stamp(tdoc['end_at'])
        cal_tdoc['penalty_since'] = self.datetime_stamp(tdoc['penalty_since'])
      else:
        cal_tdoc['end_at'] = self.datetime_stamp(tdoc['penalty_since'])
      calendar_tdocs.append(cal_tdoc)
    self.render('homework_main.html', tdocs=tdocs, calendar_tdocs=calendar_tdocs)


@app.route('/homework/{tid:\w{24}}', 'homework_detail')
class HomeworkDetailHandler(contest.ContestMixin, base.OperationHandler):
  DISCUSSIONS_PER_PAGE = 15

  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.get_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, page: int=1):
    tdoc = await contest.get(self.domain_id, document.TYPE_HOMEWORK, tid)
    tsdoc, pdict = await asyncio.gather(
        contest.get_status(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], self.user['_id']),
        problem.get_dict(self.domain_id, tdoc['pids']))
    psdict = dict()
    rdict = dict()
    if tsdoc:
      attended = tsdoc.get('attend') == 1
      for pdetail in tsdoc.get('detail', []):
        psdict[pdetail['pid']] = pdetail
      if self.can_show_record(tdoc):
        rdict = await record.get_dict((psdoc['rid'] for psdoc in psdict.values()),
                                      get_hidden=True)
      else:
        rdict = dict((psdoc['rid'], {'_id': psdoc['rid']}) for psdoc in psdict.values())
    else:
      attended = False
    # discussion
    ddocs, dpcount, dcount = await pagination.paginate(
        discussion.get_multi(self.domain_id,
                             parent_doc_type=tdoc['doc_type'],
                             parent_doc_id=tdoc['doc_id']),
        page, self.DISCUSSIONS_PER_PAGE)
    uids = set(ddoc['owner_uid'] for ddoc in ddocs)
    uids.add(tdoc['owner_uid'])
    udict = await user.get_dict(uids)
    dudict = await domain.get_dict_user_by_uid(domain_id=self.domain_id, uids=uids)
    path_components = self.build_path(
      (self.translate('homework_main'), self.reverse_url('homework_main')),
      (tdoc['title'], None))
    self.render('homework_detail.html', tdoc=tdoc, tsdoc=tsdoc, attended=attended, udict=udict,
                dudict=dudict, pdict=pdict, psdict=psdict, rdict=rdict,
                ddocs=ddocs, page=page, dpcount=dpcount, dcount=dcount,
                datetime_stamp=self.datetime_stamp,
                page_title=tdoc['title'], path_components=path_components)

  @base.route_argument
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_ATTEND_HOMEWORK)
  @base.require_csrf_token
  @base.sanitize
  async def post_attend(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, document.TYPE_HOMEWORK, tid)
    if self.is_done(tdoc):
      raise error.HomeworkNotLiveError(tdoc['doc_id'])
    await contest.attend(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/homework/{tid:\w{24}}/code', 'homework_code')
class HomeworkCodeHandler(base.OperationHandler):
  @base.limit_rate('homework_code', 3600, 60)
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_READ_RECORD_CODE)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, document.TYPE_HOMEWORK, tid)
    rnames = {}
    for tsdoc in tsdocs:
      for pdetail in tsdoc.get('detail', []):
        rnames[pdetail['rid']] = 'U{}_P{}_R{}'.format(tsdoc['uid'], pdetail['pid'], pdetail['rid'])
    output_buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(output_buffer, 'a', zipfile.ZIP_DEFLATED)
    rdocs = record.get_multi(get_hidden=True, _id={'$in': list(rnames.keys())})
    async for rdoc in rdocs:
      zip_file.writestr(rnames[rdoc['_id']] + '.' + rdoc['lang'], rdoc['code'])
    # mark all files as created in Windows :p
    for zfile in zip_file.filelist:
      zfile.create_system = 0
    zip_file.close()

    await self.binary(output_buffer.getvalue(), 'application/zip',
                      file_name='{}.zip'.format(tdoc['title']))


@app.route('/homework/{tid}/{pid:-?\d+|\w{24}}', 'homework_detail_problem')
class HomeworkDetailProblemHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, document.TYPE_HOMEWORK, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc, udoc, dudoc = await asyncio.gather(
        contest.get_status(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']),
        domain.get_user(domain_id=self.domain_id, uid=tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    if not self.is_done(tdoc):
      if not attended:
        raise error.HomeworkNotAttendedError(tdoc['doc_id'])
      if not self.is_ongoing(tdoc):
        raise error.HomeworkNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    path_components = self.build_path(
        (self.translate('homework_main'), self.reverse_url('homework_main')),
        (tdoc['title'], self.reverse_url('homework_detail', tid=tid)),
        (pdoc['title'], None))
    self.render('problem_detail.html', tdoc=tdoc, pdoc=pdoc, tsdoc=tsdoc, udoc=udoc,
                attended=attended, dudoc=dudoc,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/homework/{tid}/{pid}/submit', 'homework_detail_problem_submit')
class HomeworkDetailProblemSubmitHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, document.TYPE_HOMEWORK, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc, udoc = await asyncio.gather(
        contest.get_status(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    if not attended:
      raise error.HomeworkNotAttendedError(tdoc['doc_id'])
    if not self.is_ongoing(tdoc):
      raise error.HomeworkNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    if self.can_show_record(tdoc):
      rdocs = await record.get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id'], get_hidden=True) \
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

  @base.limit_rate('add_record', 60, 100)
  @base.route_argument
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id,
                 lang: str, code: str):
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, document.TYPE_HOMEWORK, tid),
                                      problem.get(self.domain_id, pid))
    tsdoc = await contest.get_status(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.HomeworkNotAttendedError(tdoc['doc_id'])
    if not self.is_ongoing(tdoc):
      raise error.HomeworkNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION,
                           self.user['_id'], lang, code,
                           ttype=document.TYPE_HOMEWORK, tid=tdoc['doc_id'], hidden=True)
    await contest.update_status(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], self.user['_id'],
                                rid, pdoc['doc_id'], False, 0)
    if not self.can_show_record(tdoc):
      self.json_or_redirect(self.reverse_url('homework_detail', tid=tdoc['doc_id']))
    else:
      self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/homework/{tid}/scoreboard', 'homework_scoreboard')
class HomeworkScoreboardHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK_SCOREBOARD)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, rows, udict = await self.get_scoreboard(document.TYPE_HOMEWORK, tid)
    page_title = self.translate('homework_scoreboard')
    path_components = self.build_path(
        (self.translate('homework_main'), self.reverse_url('homework_main')),
        (tdoc['title'], self.reverse_url('homework_detail', tid=tdoc['doc_id'])),
        (page_title, None))
    dudict = await domain.get_dict_user_by_uid(domain_id=self.domain_id, uids=udict.keys())
    self.render('contest_scoreboard.html', tdoc=tdoc, rows=rows, dudict=dudict,
                page_title=page_title, path_components=path_components)


@app.route('/homework/{tid}/scoreboard/download/{ext}', 'homework_scoreboard_download')
class HomeworkScoreboardDownloadHandler(contest.ContestMixin, base.Handler):
  def _export_status_as_csv(self, rows):
    # \r\n for notepad compatibility
    csv_content = '\r\n'.join([','.join([str(c['value']) for c in row]) for row in rows])
    data = '\uFEFF' + csv_content
    return data.encode()

  def _export_status_as_html(self, rows):
    return self.render_html('contest_scoreboard_download_html.html', rows=rows).encode()

  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK_SCOREBOARD)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, ext: str):
    get_status_content = {
      'csv': self._export_status_as_csv,
      'html': self._export_status_as_html,
    }
    if ext not in get_status_content:
      raise error.ValidationError('ext')
    tdoc, rows, udict = await self.get_scoreboard(document.TYPE_HOMEWORK, tid, True)
    data = get_status_content[ext](rows)
    file_name = tdoc['title']
    await self.binary(data, file_name='{}.{}'.format(file_name, ext))


@app.route('/homework/create', 'homework_create')
class HomeworkCreateHandler(contest.ContestMixin, base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_HOMEWORK)
  async def get(self):
    begin_at = self.now.replace(tzinfo=pytz.utc).astimezone(self.timezone) + datetime.timedelta(days=1)
    penalty_since = begin_at + datetime.timedelta(days=7)
    page_title = self.translate('homework_create')
    path_components = self.build_path((page_title, None))
    self.render('homework_edit.html',
                date_begin_text=begin_at.strftime('%Y-%m-%d'),
                time_begin_text='00:00',
                date_penalty_text=penalty_since.strftime('%Y-%m-%d'),
                time_penalty_text='23:59',
                pids=contest._format_pids([1000, 1001]),
                extension_days='1',
                page_title=page_title, path_components=path_components)

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
    except ValueError:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    try:
      penalty_since = datetime.datetime.strptime(penalty_since_date + ' ' + penalty_since_time, '%Y-%m-%d %H:%M')
      penalty_since = self.timezone.localize(penalty_since).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError:
      raise error.ValidationError('end_at_date', 'end_at_time')
    end_at = penalty_since + datetime.timedelta(days=extension_days)
    if begin_at >= penalty_since:
      raise error.ValidationError('end_at_date', 'end_at_time')
    if penalty_since > end_at:
      raise error.ValidationError('extension_days')
    pids = contest._parse_pids(pids)
    await self.verify_problems(pids)
    tid = await contest.add(self.domain_id, document.TYPE_HOMEWORK, title, content, self.user['_id'],
                            constant.contest.RULE_ASSIGNMENT, begin_at, end_at, pids,
                            penalty_since=penalty_since, penalty_rules=penalty_rules)
    await self.hide_problems(pids)
    self.json_or_redirect(self.reverse_url('homework_detail', tid=tid))


@app.route('/homework/{tid}/edit', 'homework_edit')
class HomeworkEditHandler(contest.ContestMixin, base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_HOMEWORK)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, document.TYPE_HOMEWORK, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_HOMEWORK_SELF):
      self.check_perm(builtin.PERM_EDIT_HOMEWORK)
    begin_at = pytz.utc.localize(tdoc['begin_at']).astimezone(self.timezone)
    penalty_since = pytz.utc.localize(tdoc['penalty_since']).astimezone(self.timezone)
    end_at = pytz.utc.localize(tdoc['end_at']).astimezone(self.timezone)
    extension_days = round((end_at - penalty_since).total_seconds() / 60 / 60 / 24, ndigits=2)
    page_title = self.translate('homework_edit')
    path_components = self.build_path(
        (self.translate('homework_main'), self.reverse_url('homework_main')),
        (tdoc['title'], self.reverse_url('homework_detail', tid=tdoc['doc_id'])),
        (page_title, None))
    self.render('homework_edit.html', tdoc=tdoc,
                date_begin_text=begin_at.strftime('%Y-%m-%d'),
                time_begin_text=begin_at.strftime('%H:%M'),
                date_penalty_text=penalty_since.strftime('%Y-%m-%d'),
                time_penalty_text=penalty_since.strftime('%H:%M'),
                extension_days=extension_days,
                penalty_rules=_format_penalty_rules_yaml(tdoc['penalty_rules']),
                pids=contest._format_pids(tdoc['pids']),
                page_title=page_title, path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.require_perm(builtin.PERM_EDIT_HOMEWORK)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, tid: objectid.ObjectId, title: str, content: str,
                 begin_at_date: str, begin_at_time: str,
                 penalty_since_date: str, penalty_since_time: str,
                 extension_days: float, penalty_rules: str,
                 pids: str):
    tdoc = await contest.get(self.domain_id, document.TYPE_HOMEWORK, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_HOMEWORK_SELF):
      self.check_perm(builtin.PERM_EDIT_HOMEWORK)
    penalty_rules = _parse_penalty_rules_yaml(penalty_rules)
    try:
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = self.timezone.localize(begin_at).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    try:
      penalty_since = datetime.datetime.strptime(penalty_since_date + ' ' + penalty_since_time, '%Y-%m-%d %H:%M')
      penalty_since = self.timezone.localize(penalty_since).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError:
      raise error.ValidationError('end_at_date', 'end_at_time')
    end_at = penalty_since + datetime.timedelta(days=extension_days)
    if begin_at >= penalty_since:
      raise error.ValidationError('end_at_date', 'end_at_time')
    if penalty_since > end_at:
      raise error.ValidationError('extension_days')
    pids = contest._parse_pids(pids)
    await self.verify_problems(pids)
    await contest.edit(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'], title=title, content=content,
                       begin_at=begin_at, end_at=end_at, pids=pids,
                       penalty_since=penalty_since, penalty_rules=penalty_rules)
    await self.hide_problems(pids)
    if tdoc['begin_at'] != begin_at \
        or tdoc['end_at'] != end_at \
        or tdoc['penalty_since'] != penalty_since \
        or set(tdoc['pids']) != set(pids):
      await contest.recalc_status(self.domain_id, document.TYPE_HOMEWORK, tdoc['doc_id'])
    self.json_or_redirect(self.reverse_url('homework_detail', tid=tid))
