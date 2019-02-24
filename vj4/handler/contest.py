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


@app.route('/contest', 'contest_main')
class ContestMainHandler(contest.ContestMixin, base.Handler):
  CONTESTS_PER_PAGE = 20

  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.get_argument
  @base.sanitize
  async def get(self, *, rule: int=0, page: int=1):
    if not rule:
      tdocs = contest.get_multi(self.domain_id, document.TYPE_CONTEST)
      qs = ''
    else:
      if rule not in constant.contest.CONTEST_RULES:
        raise error.ValidationError('rule')
      tdocs = contest.get_multi(self.domain_id, document.TYPE_CONTEST, rule=rule)
      qs = 'rule={0}'.format(rule)
    tdocs, tpcount, _ = await pagination.paginate(tdocs, page, self.CONTESTS_PER_PAGE)
    tsdict = await contest.get_dict_status(self.domain_id, self.user['_id'], document.TYPE_CONTEST,
                                          (tdoc['doc_id'] for tdoc in tdocs))
    self.render('contest_main.html', page=page, tpcount=tpcount, qs=qs, rule=rule,
                tdocs=tdocs, tsdict=tsdict)


@app.route('/contest/{tid:\w{24}}', 'contest_detail')
class ContestDetailHandler(contest.ContestMixin, base.OperationHandler):
  DISCUSSIONS_PER_PAGE = 15

  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.get_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, page: int=1):
    tdoc = await contest.get(self.domain_id, document.TYPE_CONTEST, tid)
    tsdoc, pdict = await asyncio.gather(
        contest.get_status(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'], self.user['_id']),
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
      (self.translate('contest_main'), self.reverse_url('contest_main')),
      (tdoc['title'], None))
    self.render('contest_detail.html', tdoc=tdoc, tsdoc=tsdoc, attended=attended, udict=udict,
                dudict=dudict, pdict=pdict, psdict=psdict, rdict=rdict,
                ddocs=ddocs, page=page, dpcount=dpcount, dcount=dcount,
                datetime_stamp=self.datetime_stamp,
                page_title=tdoc['title'], path_components=path_components)

  @base.route_argument
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_ATTEND_CONTEST)
  @base.require_csrf_token
  @base.sanitize
  async def post_attend(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, document.TYPE_CONTEST, tid)
    if self.is_done(tdoc):
      raise error.ContestNotLiveError(tdoc['doc_id'])
    await contest.attend(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'], self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/contest/{tid:\w{24}}/code', 'contest_code')
class ContestCodeHandler(base.OperationHandler):
  @base.limit_rate('contest_code', 3600, 60)
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_READ_RECORD_CODE)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, document.TYPE_CONTEST, tid)
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


@app.route('/contest/{tid}/{pid:-?\d+|\w{24}}', 'contest_detail_problem')
class ContestDetailProblemHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, document.TYPE_CONTEST, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc, udoc, dudoc = await asyncio.gather(
        contest.get_status(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']),
        domain.get_user(domain_id=self.domain_id, uid=tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    if not self.is_done(tdoc):
      if not attended:
        raise error.ContestNotAttendedError(tdoc['doc_id'])
      if not self.is_ongoing(tdoc):
        raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
        (pdoc['title'], None))
    self.render('problem_detail.html', tdoc=tdoc, pdoc=pdoc, tsdoc=tsdoc, udoc=udoc,
                attended=attended, dudoc=dudoc,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/contest/{tid}/{pid}/submit', 'contest_detail_problem_submit')
class ContestDetailProblemSubmitHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, document.TYPE_CONTEST, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc, udoc = await asyncio.gather(
        contest.get_status(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    if not attended:
      raise error.ContestNotAttendedError(tdoc['doc_id'])
    if not self.is_ongoing(tdoc):
      raise error.ContestNotLiveError(tdoc['doc_id'])
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
          (self.translate('contest_main'), self.reverse_url('contest_main')),
          (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
          (pdoc['title'], self.reverse_url('contest_detail_problem', tid=tid, pid=pid)),
          (self.translate('contest_detail_problem_submit'), None))
      self.render('problem_submit.html', tdoc=tdoc, pdoc=pdoc, rdocs=rdocs,
                  tsdoc=tsdoc, udoc=udoc, attended=attended,
                  page_title=pdoc['title'], path_components=path_components)
    else:
      self.json({'rdocs': rdocs})

  @base.limit_rate('add_record', 60, 100)
  @base.route_argument
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id,
                 lang: str, code: str):
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, document.TYPE_CONTEST, tid),
                                      problem.get(self.domain_id, pid))
    tsdoc = await contest.get_status(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'],
                                     self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.ContestNotAttendedError(tdoc['doc_id'])
    if not self.is_ongoing(tdoc):
      raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION,
                           self.user['_id'], lang, code,
                           ttype=document.TYPE_CONTEST, tid=tdoc['doc_id'], hidden=True)
    await contest.update_status(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'], self.user['_id'],
                                rid, pdoc['doc_id'], False, 0)
    if not self.can_show_record(tdoc):
      self.json_or_redirect(self.reverse_url('contest_detail', tid=tdoc['doc_id']))
    else:
      self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/contest/{tid}/scoreboard', 'contest_scoreboard')
class ContestScoreboardHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_VIEW_CONTEST_SCOREBOARD)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, rows, udict = await self.get_scoreboard(document.TYPE_CONTEST, tid)
    page_title = self.translate('contest_scoreboard')
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], self.reverse_url('contest_detail', tid=tdoc['doc_id'])),
        (page_title, None))
    dudict = await domain.get_dict_user_by_uid(domain_id=self.domain_id, uids=udict.keys())
    self.render('contest_scoreboard.html', tdoc=tdoc, rows=rows, dudict=dudict,
                page_title=page_title, path_components=path_components)


@app.route('/contest/{tid}/scoreboard/download/{ext}', 'contest_scoreboard_download')
class ContestScoreboardDownloadHandler(contest.ContestMixin, base.Handler):
  def _export_status_as_csv(self, rows):
    # \r\n for notepad compatibility
    csv_content = '\r\n'.join([','.join([str(c['value']) for c in row]) for row in rows])
    data = '\uFEFF' + csv_content
    return data.encode()

  def _export_status_as_html(self, rows):
    return self.render_html('contest_scoreboard_download_html.html', rows=rows).encode()

  @base.route_argument
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_VIEW_CONTEST_SCOREBOARD)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, ext: str):
    get_status_content = {
      'csv': self._export_status_as_csv,
      'html': self._export_status_as_html,
    }
    if ext not in get_status_content:
      raise error.ValidationError('ext')
    tdoc, rows, udict = await self.get_scoreboard(document.TYPE_CONTEST, tid, True)
    data = get_status_content[ext](rows)
    file_name = tdoc['title']
    await self.binary(data, file_name='{}.{}'.format(file_name, ext))


@app.route('/contest/create', 'contest_create')
class ContestCreateHandler(contest.ContestMixin, base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  async def get(self):
    dt = self.now.replace(tzinfo=pytz.utc).astimezone(self.timezone)
    ts = calendar.timegm(dt.utctimetuple())
    # find next quarter
    ts = ts - ts % (15 * 60) + 15 * 60
    dt = datetime.datetime.fromtimestamp(ts, self.timezone)
    self.render('contest_edit.html',
                date_text=dt.strftime('%Y-%m-%d'),
                time_text=dt.strftime('%H:%M'),
                pids=contest._format_pids([1000, 1001]))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, title: str, content: str, rule: int,
                 begin_at_date: str, begin_at_time: str, duration: float,
                 pids: str):
    try:
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = self.timezone.localize(begin_at).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    end_at = begin_at + datetime.timedelta(hours=duration)
    if begin_at >= end_at:
      raise error.ValidationError('duration')
    pids = contest._parse_pids(pids)
    await self.verify_problems(pids)
    tid = await contest.add(self.domain_id, document.TYPE_CONTEST, title, content, self.user['_id'],
                            rule, begin_at, end_at, pids)
    await self.hide_problems(pids)
    self.json_or_redirect(self.reverse_url('contest_detail', tid=tid))


@app.route('/contest/{tid}/edit', 'contest_edit')
class ContestEditHandler(contest.ContestMixin, base.Handler):
  @base.route_argument
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_CONTEST)
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, document.TYPE_CONTEST, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_CONTEST_SELF):
      self.check_perm(builtin.PERM_EDIT_CONTEST)
    dt = pytz.utc.localize(tdoc['begin_at']).astimezone(self.timezone)
    duration = (tdoc['end_at'] - tdoc['begin_at']).total_seconds() / 3600
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], self.reverse_url('contest_detail', tid=tdoc['doc_id'])),
        (self.translate('contest_edit'), None))
    self.render('contest_edit.html', tdoc=tdoc,
                date_text=dt.strftime('%Y-%m-%d'),
                time_text=dt.strftime('%H:%M'),
                duration=duration,
                pids=contest._format_pids(tdoc['pids']),
                path_components=path_components)

  @base.route_argument
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.require_perm(builtin.PERM_EDIT_CONTEST)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, tid: objectid.ObjectId, title: str, content: str, rule: int,
                 begin_at_date: str=None, begin_at_time: str=None, duration: float,
                 pids: str):
    tdoc = await contest.get(self.domain_id, document.TYPE_CONTEST, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_CONTEST_SELF):
      self.check_perm(builtin.PERM_EDIT_CONTEST)
    try:
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = self.timezone.localize(begin_at).astimezone(pytz.utc).replace(tzinfo=None)
    except ValueError:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    end_at = begin_at + datetime.timedelta(hours=duration)
    if begin_at >= end_at:
      raise error.ValidationError('duration')
    pids = contest._parse_pids(pids)
    await self.verify_problems(pids)
    await contest.edit(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'], title=title, content=content,
                       rule=rule, begin_at=begin_at, end_at=end_at, pids=pids)
    await self.hide_problems(pids)
    if tdoc['begin_at'] != begin_at \
        or tdoc['end_at'] != end_at \
        or set(tdoc['pids']) != set(pids) \
        or tdoc['rule'] != rule:
      await contest.recalc_status(self.domain_id, document.TYPE_CONTEST, tdoc['doc_id'])
    self.json_or_redirect(self.reverse_url('contest_detail', tid=tdoc['doc_id']))
