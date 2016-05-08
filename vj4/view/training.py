from bson import objectid
from vj4 import app
from vj4.controller import training
from vj4.model import builtin
from vj4.view import base

@app.route('/training', 'training_main')
class TrainingMainView(base.View):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  async def get(self):
    tdocs = await training.get_list_by_user(self.domain_id, self.user['_id'])
    self.render('training_main.html', tdocs=tdocs)

@app.route('/training/{tid}', 'training_detail')
class TrainingDetailView(base.View):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  @base.route_argument
  async def get(self, *, tid):
    tdoc = await training.check(self.domain_id, objectid.ObjectId(tid), self.user['_id'])
    path_components = self.build_path(('training_main', self.reverse_url('training_main')),
                                      (tdoc['title'], None))
    self.render('training_detail.html', tdoc=tdoc, path_components=path_components)
