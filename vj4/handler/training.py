from bson import objectid

from vj4 import app
from vj4.model import builtin
from vj4.model.adaptor import training
from vj4.handler import base


@app.route('/training', 'training_main')
class TrainingMainHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  # TODO: permission need to be changed
  async def get(self):
    tdocs = await training.get_list_by_user(self.domain_id, self.user['_id'])
    self.render('training_main.html', tdocs=tdocs)


@app.route('/training/enrolled', 'training_enrolled')
class TrainingEnrolledHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  async def get(self):
    # TODO: twd2
    self.render('training_enrolled.html')


@app.route('/training/create', 'training_create')
class TrainingCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  async def get(self):
    # TODO: twd2
    self.render('training_create.html')


@app.route('/training/owned', 'training_owned')
class TrainingOwnedHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  async def get(self):
    # TODO: twd2
    self.render('training_owned.html')


@app.route('/training/detail', 'training_detail_demo')
class TrainingDetailDemoHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  async def get(self):
    # TODO: for demo purpose only. remove this handler!
    self.render('training_detail.html')


@app.route('/training/{tid}', 'training_detail')
class TrainingDetailHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await training.check(self.domain_id, tid, self.user['_id'])
    path_components = self.build_path(
      (self.translate('training_main'), self.reverse_url('training_main')),
      (tdoc['title'], None))
    self.render('training_detail.html', tdoc=tdoc, path_components=path_components)
