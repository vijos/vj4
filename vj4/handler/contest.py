import asyncio
import calendar
import datetime
import functools
import io
import pytz
import zipfile
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import opcount
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.handler import base
from vj4.util import pagination


class ContestStatusMixin(object):
  @property
  @functools.lru_cache()
  def now(self):
    # TODO(iceboy): This does not work on multi-machine environment.
    return datetime.datetime.utcnow()

  def is_new(self, tdoc):
    ready_at = tdoc['begin_at'] - datetime.timedelta(days=1)
    return self.now < ready_at

  def is_ready(self, tdoc):
    ready_at = tdoc['begin_at'] - datetime.timedelta(days=1)
    return ready_at <= self.now < tdoc['begin_at']

  def is_live(self, tdoc):
    return tdoc['begin_at'] <= self.now < tdoc['end_at']

  def is_done(self, tdoc):
    return tdoc['end_at'] <= self.now

  def status_text(self, tdoc):
    if self.is_new(tdoc):
      return 'New'
    elif self.is_ready(tdoc):
      return 'Ready (☆▽☆)'
    elif self.is_live(tdoc):
      return 'Live...'
    else:
      return 'Done'

  def can_show(self, tdoc):
    return contest.RULES[tdoc['rule']].show_func(tdoc, self.now)


@app.route('/contest', 'contest_main')
class ContestMainHandler(base.Handler, ContestStatusMixin):
  CONTESTS_PER_PAGE = 20

  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.get_argument
  @base.sanitize
  async def get(self, *, rule: str=None, page: int=1):
    if not rule:
      tdocs = contest.get_multi(self.domain_id)
      qs = ''
    else:
      tdocs = contest.get_multi(self.domain_id, rule=int(rule))
      qs = 'rule={0}'.format(int(rule))
    tdocs, tpcount, _ = await pagination.paginate(tdocs, page, self.CONTESTS_PER_PAGE)
    tsdict = await contest.get_dict_status(self.domain_id, self.user['_id'],
                                           (tdoc['doc_id'] for tdoc in tdocs))
    self.render('contest_main.html', page=page, tpcount=tpcount, qs=qs,
                tdocs=tdocs, tsdict=tsdict)


@app.route('/contest/{tid:\w{24}}', 'contest_detail')
class ContestDetailHandler(base.OperationHandler, ContestStatusMixin):
  DISCUSSIONS_PER_PAGE = 15

  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, page: int=1):
    # contest
    tdoc = await contest.get(self.domain_id, tid)
    tsdoc, pdict = await asyncio.gather(
        contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        problem.get_dict(self.domain_id, tdoc['pids']))
    psdict = dict()
    rdict = dict()
    if tsdoc:
      attended = tsdoc.get('attend') == 1
      for pdetail in tsdoc.get('detail', []):
        psdict[pdetail['pid']] = pdetail
      if contest.RULES[tdoc['rule']].show_func(tdoc, self.now) \
         or self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS):
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
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], None))
    self.render('contest_detail.html', tdoc=tdoc, tsdoc=tsdoc, attended=attended, udict=udict,
                pdict=pdict, psdict=psdict, rdict=rdict,
                ddocs=ddocs, page=page, dpcount=dpcount, dcount=dcount,
                datetime_stamp=self.datetime_stamp,
                page_title=tdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_ATTEND_CONTEST)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_attend(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, tid)
    if self.is_done(tdoc):
      raise error.ContestNotLiveError(tdoc['doc_id'])
    await contest.attend(self.domain_id, tdoc['doc_id'], self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/contest/{tid:\w{24}}/code', 'contest_code')
class ContestCodeHandler(base.OperationHandler):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_READ_RECORD_CODE)
  @base.limit_rate('contest_code')
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, tid)
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

    await self.binary(output_buffer.getvalue(), 'application/zip')


@app.route('/contest/{tid}/{pid:-?\d+|\w{24}}', 'contest_detail_problem')
class ContestDetailProblemHandler(base.Handler, ContestStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    if not self.is_done(tdoc):
      tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
      if not tsdoc or tsdoc.get('attend') != 1:
        raise error.ContestNotAttendedError(tdoc['doc_id'])
      if not self.is_live(tdoc):
        raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    tsdoc, udoc = await asyncio.gather(
        contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], self.reverse_url('contest_detail', tid=tid)),
        (pdoc['title'], None))
    self.render('problem_detail.html', tdoc=tdoc, pdoc=pdoc, tsdoc=tsdoc, udoc=udoc,
                attended=attended,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/contest/{tid}/{pid}/submit', 'contest_detail_problem_submit')
class ContestDetailProblemSubmitHandler(base.Handler, ContestStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid, uid))
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.ContestNotAttendedError(tdoc['doc_id'])
    if not self.is_live(tdoc):
      raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    tsdoc, udoc = await asyncio.gather(
        contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        user.get_by_uid(tdoc['owner_uid']))
    attended = tsdoc and tsdoc.get('attend') == 1
    if (contest.RULES[tdoc['rule']].show_func(tdoc, self.now)
        or self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
      rdocs = await record.get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id']) \
                          .sort([('_id', -1)]) \
                          .to_list(10)
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


  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *,
                 tid: objectid.ObjectId, pid: document.convert_doc_id, lang: str, code: str):
    await opcount.inc(**opcount.OPS['run_code'], ident=opcount.PREFIX_USER + str(self.user['_id']))
    tdoc, pdoc = await asyncio.gather(contest.get(self.domain_id, tid),
                                      problem.get(self.domain_id, pid))
    tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
    if not tsdoc or tsdoc.get('attend') != 1:
      raise error.ContestNotAttendedError(tdoc['doc_id'])
    if not self.is_live(tdoc):
      raise error.ContestNotLiveError(tdoc['doc_id'])
    if pid not in tdoc['pids']:
      raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION,
                           self.user['_id'], lang, code, tid=tdoc['doc_id'], hidden=True)
    await contest.update_status(self.domain_id, tdoc['_id'], self.user['_id'],
                                rid, pdoc['doc_id'], False, 0)
    if (not contest.RULES[tdoc['rule']].show_func(tdoc, self.now)
        and not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
        self.json_or_redirect(self.reverse_url('contest_detail', tid=tdoc['_id']))
    else:
      self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/contest/{tid}/status', 'contest_status')
class ContestStatusHandler(base.Handler, ContestStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.require_perm(builtin.PERM_VIEW_CONTEST_STATUS)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, tid)
    if (not contest.RULES[tdoc['rule']].show_func(tdoc, self.now)
        and not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
      raise error.ContestStatusHiddenError()
    udict, pdict = await asyncio.gather(user.get_dict([tsdoc['uid'] for tsdoc in tsdocs]),
                                        problem.get_dict(self.domain_id, tdoc['pids']))
    ranked_tsdocs = contest.RULES[tdoc['rule']].rank_func(tsdocs)
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], self.reverse_url('contest_detail', tid=tdoc['doc_id'])),
        (self.translate('contest_status'), None))
    self.render('contest_status.html', tdoc=tdoc, ranked_tsdocs=ranked_tsdocs, dict=dict,
                udict=udict, pdict=pdict, path_components=path_components)


@app.route('/contest/create', 'contest_create')
class ContestCreateHandler(base.Handler, ContestStatusMixin):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  async def get(self):
    dt = self.now.replace(tzinfo=pytz.utc).astimezone(self.timezone)
    ts = calendar.timegm(dt.utctimetuple())
    # find next quarter
    ts = ts - ts % (15 * 60) + 15 * 60
    dt = datetime.datetime.fromtimestamp(ts, self.timezone)
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
      begin_at = datetime.datetime.strptime(begin_at_date + ' ' + begin_at_time, '%Y-%m-%d %H:%M')
      begin_at = self.timezone.localize(begin_at).astimezone(pytz.utc).replace(tzinfo=None)
      end_at = begin_at + datetime.timedelta(hours=duration)
    except ValueError as e:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    if begin_at <= self.now:
      raise error.ValidationError('begin_at_date', 'begin_at_time')
    if begin_at >= end_at:
      raise error.ValidationError('duration')
    pids = list(set(map(document.convert_doc_id, pids.split(','))))
    pdocs = await problem.get_multi(domain_id=self.domain_id, doc_id={'$in': pids},
                                    fields={'doc_id': 1}) \
                         .sort('doc_id', 1) \
                         .to_list(None)
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
