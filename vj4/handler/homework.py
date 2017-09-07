import asyncio
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.handler import base
from vj4.handler import contest as contestHandler
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

  def status_text(self, tdoc):
    if self.is_new(tdoc):
      return 'Ready'
    if self.is_live(tdoc):
      return 'Open'
    elif self.is_extend(tdoc):
      return 'Open (Extend)'
    else:
      return 'Finished'

@app.route('/homework', 'homework_main')
class HomeworkMainHandler(base.Handler, HomeworkStatusMixin):
  HOMEWORK_PER_PAGE = 20

  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.get_argument
  @base.sanitize
  async def get(self, *, page: int=1):
    tdocs = contest.get_multi(self.domain_id, rule={'$in': constant.contest.HOMEWORK_RULES})
    tdocs, tpcount, _ = await pagination.paginate(tdocs, page, self.HOMEWORK_PER_PAGE)
    tsdict = await contest.get_dict_status(self.domain_id, self.user['_id'],
                                           (tdoc['doc_id'] for tdoc in tdocs))
    self.render('homework_main.html', page=page, tpcount=tpcount, tdocs=tdocs, tsdict=tsdict)


@app.route('/homework/{tid:\w{24}}', 'homework_detail')
class HomeworkDetailHandler(base.OperationHandler, HomeworkStatusMixin):
  @base.require_perm(builtin.PERM_VIEW_HOMEWORK)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId, page: int=1):
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
                page=page, page_title=tdoc['title'], path_components=path_components)

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
