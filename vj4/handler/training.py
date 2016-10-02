import asyncio
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4.model import builtin
from vj4.model import document
from vj4.model.adaptor import problem
from vj4.model.adaptor import training
from vj4.handler import base


class TrainingMixin(object):
  def get_pids(self, tdoc):
    pids = set()
    for node in tdoc['dag']:
      for pid in node['pids']:
        pids.add(pid)
    return list(pids)

  def is_done(self, node, done_nids, done_pids):
    return set(done_nids) >= set(node['require_nids']) \
           and set(done_pids) >= set(node['pids'])

  def is_progress(self, node, done_nids, done_pids, prog_pids):
    return set(done_nids) >= set(node['require_nids']) \
           and not set(done_pids) >= set(node['pids']) \
           and (set(prog_pids) & set(node['pids']))

  def is_open(self, node, done_nids, done_pids, prog_pids):
    return set(done_nids) >= set(node['require_nids']) \
           and not set(done_pids) >= set(node['pids']) \
           and not (set(prog_pids) & set(node['pids']))

  def is_invalid(self, node, done_nids):
    return not set(done_nids) >= set(node['require_nids'])


@app.route('/training', 'training_main')
class TrainingMainHandler(base.Handler, TrainingMixin):
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  async def get(self):
    tdocs = await training.get_multi(self.domain_id).to_list(None)
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


@app.route('/training/{tid}', 'training_detail')
class TrainingDetailHandler(base.Handler, TrainingMixin):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  @base.route_argument
  @base.sanitize
  async def get(self, tid: objectid.ObjectId):
    tdoc = await training.get(self.domain_id, tid)
    pids = self.get_pids(tdoc)
    tsdoc, pdict, psdict = await asyncio.gather(
        training.get_status(self.domain_id, tdoc['doc_id'], self.user['_id']),
        problem.get_dict_same_domain(self.domain_id, pids),
        problem.get_dict_status(self.domain_id, self.user['_id'], pids))
    done_pids = set()
    prog_pids = set()
    for pid, psdoc in psdict.items():
      if 'status' in psdoc:
        if psdoc['status'] == constant.record.STATUS_ACCEPTED:
          done_pids.add(pid)
        else:
          prog_pids.add(pid)
    nsdict = {}
    ndict = {}
    for node in tdoc['dag']:
      ndict[node['_id']] = node
      total_count = len(node['require_nids']) + len(node['pids'])
      if tsdoc:
        done_count = len(set(node['require_nids']) & set(tsdoc.get('done_nids', []))) \
                     + len(set(node['pids']) & set(done_pids))
      else:
        done_count = 0
      nsdoc = {'progress': int(100 * done_count / total_count) if total_count else 100}
      nsdict[node['_id']] = nsdoc
    path_components = self.build_path(
      (self.translate('training_main'), self.reverse_url('training_main')),
      (tdoc['title'], None))
    self.render('training_detail.html', tdoc=tdoc, tsdoc=tsdoc, pids=pids, pdict=pdict,
                psdict=psdict, done_pids=list(done_pids), prog_pids=list(prog_pids),
                ndict=ndict, nsdict=nsdict,
                path_components=path_components)
