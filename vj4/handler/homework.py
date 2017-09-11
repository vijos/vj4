import asyncio
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
from vj4.handler import contest as contestHandler
from vj4.handler import problem as problemHandler
from vj4.util import pagination

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


#   @base.require_priv(builtin.PRIV_USER_PROFILE)
#   @base.require_perm(builtin.PERM_VIEW_CONTEST)
#   @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
#   @base.route_argument
#   @base.post_argument
#   @base.require_csrf_token
#   @base.sanitize
#   async def post(self, *,
#                  tid: objectid.ObjectId, pid: document.convert_doc_id, lang: str, code: str):
#     await opcount.inc(**opcount.OPS['run_code'], ident=opcount.PREFIX_USER + str(self.user['_id']))
#     tdoc, pdoc = await asyncio.gather(contest.get_contest(self.domain_id, tid),
#                                       problem.get(self.domain_id, pid))
#     tsdoc = await contest.get_status(self.domain_id, tdoc['doc_id'], self.user['_id'])
#     if not tsdoc or tsdoc.get('attend') != 1:
#       raise error.ContestNotAttendedError(tdoc['doc_id'])
#     if not self.is_live(tdoc):
#       raise error.ContestNotLiveError(tdoc['doc_id'])
#     if pid not in tdoc['pids']:
#       raise error.ProblemNotFoundError(self.domain_id, pid, tdoc['doc_id'])
#     rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION,
#                            self.user['_id'], lang, code, tid=tdoc['doc_id'], hidden=True)
#     await contest.update_status(self.domain_id, tdoc['doc_id'], self.user['_id'],
#                                 rid, pdoc['doc_id'], False, 0)
#     if (not contest.RULES[tdoc['rule']].show_func(tdoc, self.now)
#         and not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)):
#         self.json_or_redirect(self.reverse_url('contest_detail', tid=tdoc['doc_id']))
#     else:
#       self.json_or_redirect(self.reverse_url('record_detail', rid=rid))
