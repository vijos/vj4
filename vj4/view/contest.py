from bson import objectid
from vj4 import app
from vj4.model import builtin
from vj4.controller import contest
from vj4.view import base

STATUS_TEXTS = {
  contest.STATUS_NEW: 'New',
  contest.STATUS_READY: 'Ready',
  contest.STATUS_LIVE: 'Live',
  contest.STATUS_DONE: 'Done',
}

TYPE_TEXTS = {
  contest.RULE_ACM: 'ACM/ICPC',
  contest.RULE_OI: 'OI',
}

@app.route('/tests', 'contest_main')
class ContestMainView(base.View):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  async def get(self):
    tdocs = await contest.get_list(self.domain_id)
    self.render('contest_main.html', tdocs=tdocs)

@app.route('/tests/{tid:\w{24}}', 'contest_detail')
class ContestDetailView(base.View):
  @base.require_perm(builtin.PERM_VIEW_CONTEST)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await contest.get(self.domain_id, tid)
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], None))
    self.render('contest_detail.html', tdoc=tdoc, path_components=path_components)

@app.route('/tests/{tid:\w{24}}/status', 'contest_status')
class ContestStatusView(base.View):
  @base.require_perm(builtin.PERM_VIEW_CONTEST_STATUS)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc, tsdocs = await contest.get_and_list_status(self.domain_id, tid)
    path_components = self.build_path(
        (self.translate('contest_main'), self.reverse_url('contest_main')),
        (tdoc['title'], self.reverse_url('contest_detail', tid=tdoc['doc_id'])),
        (self.translate('contest_status'), None))
    self.render('contest_status.html', tdoc=tdoc, tsdocs=tsdocs, path_components=path_components)

@app.route('/tests/create', 'contest_create')
class ContestMainView(base.View):
  @base.require_perm(builtin.PERM_CREATE_CONTEST)
  async def get(self):
    self.render('contest_create.html')
