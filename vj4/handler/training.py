import asyncio
from json import decoder
from bson import objectid

from vj4 import app
from vj4 import error
from vj4 import constant
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import user
from vj4.model.adaptor import problem
from vj4.model.adaptor import training
from vj4.handler import base
from vj4.util import json
from vj4.util import pagination
from vj4.util import misc


def _parse_dag_json(dag):
  try:
    dag = json.decode(dag)
  except decoder.JSONDecodeError:
    raise error.ValidationError('dag') from None
  if not isinstance(dag, list):
    raise error.ValidationError('dag')
  new_dag = []
  try:
    for node in dag:
      if any(k not in node for k in ['_id', 'require_nids', 'pids']):
        raise error.ValidationError('dag')
      new_node = {'_id': int(node['_id']),
                  'title': str(node.get('title', '')),
                  'require_nids': misc.dedupe(map(int, node['require_nids'])),
                  'pids': misc.dedupe(map(document.convert_doc_id, node['pids']))}
      new_dag.append(new_node)
  except ValueError:
    raise error.ValidationError('dag') from None
  return new_dag


class TrainingMixin(object):
  def get_pids(self, tdoc):
    pids = set()
    for node in tdoc['dag']:
      pids.update(node['pids'])
    return list(pids)

  def is_done(self, node, done_nids, done_pids):
    return set(done_nids) >= set(node['require_nids']) \
           and set(done_pids) >= set(node['pids'])

  def is_progress(self, node, done_nids, done_pids, prog_pids):
    return set(done_nids) >= set(node['require_nids']) \
           and not set(done_pids) >= set(node['pids']) \
           and ((set(done_pids) | set(prog_pids)) & set(node['pids']))

  def is_open(self, node, done_nids, done_pids, prog_pids):
    return set(done_nids) >= set(node['require_nids']) \
           and not set(done_pids) >= set(node['pids']) \
           and not ((set(done_pids) | set(prog_pids)) & set(node['pids']))

  def is_invalid(self, node, done_nids):
    return not set(done_nids) >= set(node['require_nids'])


@app.route('/training', 'training_main')
class TrainingMainHandler(base.Handler, TrainingMixin):
  TRAININGS_PER_PAGE = 20

  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  @base.get_argument
  @base.sanitize
  async def get(self, *, sort: str='', page: int=1):
    if sort:
      qs = 'sort={0}'.format(sort)
    else:
      qs = ''
    tdocs, tpcount, _ = await pagination.paginate(training.get_multi(self.domain_id) \
                                                          .sort('doc_id', 1),
                                                  page, self.TRAININGS_PER_PAGE)
    tids = set(tdoc['doc_id'] for tdoc in tdocs)
    tsdict = dict()
    tdict = dict()
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      enrolled_tids = set()
      async for tsdoc in training.get_multi_status(domain_id=self.domain_id,
                                                   uid=self.user['_id'],
                                                   **{'$or': [{'doc_id': {'$in': list(tids)}},
                                                              {'enroll': 1}]}):
        tsdict[tsdoc['doc_id']] = tsdoc
        enrolled_tids.add(tsdoc['doc_id'])
      enrolled_tids -= tids
      if enrolled_tids:
        tdict = await training.get_dict(self.domain_id, enrolled_tids)
    for tdoc in tdocs:
      tdict[tdoc['doc_id']] = tdoc
    self.render('training_main.html', tdocs=tdocs, page=page, tpcount=tpcount, qs=qs,
                tsdict=tsdict, tdict=tdict)


@app.route('/training/{tid:\w{24}}', 'training_detail')
class TrainingDetailHandler(base.OperationHandler, TrainingMixin):
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  @base.route_argument
  @base.sanitize
  async def get(self, tid: objectid.ObjectId):
    tdoc = await training.get(self.domain_id, tid)
    pids = self.get_pids(tdoc)
    # TODO(twd2): check status, eg. test, hidden problem, ...
    if not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      f = {'hidden': False}
    else:
      f = {}
    owner_udoc, owner_dudoc, pdict = await asyncio.gather(
        user.get_by_uid(tdoc['owner_uid']),
        domain.get_user(domain_id=self.domain_id, uid=tdoc['owner_uid']),
        problem.get_dict(self.domain_id, pids, **f))
    psdict = await problem.get_dict_status(self.domain_id,
                                           self.user['_id'], pdict.keys())
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
    done_nids = set()
    for node in tdoc['dag']:
      ndict[node['_id']] = node
      total_count = len(node['pids'])
      done_count = len(set(node['pids']) & set(done_pids))
      nsdoc = {'progress': int(100 * done_count / total_count) if total_count else 100,
               'is_done': self.is_done(node, done_nids, done_pids),
               'is_progress': self.is_progress(node, done_nids, done_pids, prog_pids),
               'is_open': self.is_open(node, done_nids, done_pids, prog_pids),
               'is_invalid': self.is_invalid(node, done_nids)}
      if nsdoc['is_done']:
        done_nids.add(node['_id'])
      nsdict[node['_id']] = nsdoc
    tsdoc = await training.set_status(self.domain_id, tdoc['doc_id'], self.user['_id'],
                                      done_nids=list(done_nids), done_pids=list(done_pids),
                                      done=len(done_nids) == len(tdoc['dag']))
    path_components = self.build_path(
        (self.translate('training_main'), self.reverse_url('training_main')),
        (tdoc['title'], None))
    self.render('training_detail.html', tdoc=tdoc, tsdoc=tsdoc, pids=pids,
                pdict=pdict, psdict=psdict, ndict=ndict, nsdict=nsdict,
                owner_udoc=owner_udoc, owner_dudoc=owner_dudoc,
                page_title=tdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_TRAINING)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_enroll(self, *, tid: objectid.ObjectId):
    tdoc = await training.get(self.domain_id, tid)
    await training.enroll(self.domain_id, tdoc['doc_id'], self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/training/create', 'training_create')
class TrainingCreateHandler(base.Handler, TrainingMixin):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_TRAINING)
  async def get(self):
    self.render('training_edit.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_TRAINING)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, title: str, content: str, dag: str, desc: str):
    dag = _parse_dag_json(dag)
    pids = self.get_pids({'dag': dag})
    if not pids:
      # empty plan
      raise error.ValidationError('dag')
    pdocs = await problem.get_multi(domain_id=self.domain_id, doc_id={'$in': pids},
                                    fields={'doc_id': 1, 'hidden': 1}) \
                         .sort('doc_id', 1) \
                         .to_list()
    exist_pids = [pdoc['doc_id'] for pdoc in pdocs]
    if len(pids) != len(exist_pids):
      for pid in pids:
        if pid not in exist_pids:
          raise error.ProblemNotFoundError(self.domain_id, pid)
    for pdoc in pdocs:
      if pdoc.get('hidden', False):
        self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    tid = await training.add(self.domain_id, title, content, self.user['_id'],
                             dag=dag, desc=desc)
    self.json_or_redirect(self.reverse_url('training_detail', tid=tid))


@app.route('/training/{tid}/edit', 'training_edit')
class TrainingEditHandler(base.Handler, TrainingMixin):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.sanitize
  async def get(self, *, tid: objectid.ObjectId):
    tdoc = await training.get(self.domain_id, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_TRAINING_SELF):
      self.check_perm(builtin.PERM_EDIT_TRAINING)
    dag = json.encode_pretty(tdoc['dag'])
    path_components = self.build_path(
        (self.translate('training_main'), self.reverse_url('training_main')),
        (tdoc['title'], self.reverse_url('training_detail', tid=tdoc['doc_id'])),
        (self.translate('training_edit'), None))
    self.render('training_edit.html', tdoc=tdoc, dag=dag,
                page_title=tdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, tid: objectid.ObjectId, title: str, content: str, dag: str, desc: str):
    tdoc = await training.get(self.domain_id, tid)
    if not self.own(tdoc, builtin.PERM_EDIT_TRAINING_SELF):
      self.check_perm(builtin.PERM_EDIT_TRAINING)
    dag = _parse_dag_json(dag)
    pids = self.get_pids({'dag': dag})
    if not pids:
      # empty plan
      raise error.ValidationError('dag')
    pdocs = await problem.get_multi(domain_id=self.domain_id, doc_id={'$in': pids},
                                    fields={'doc_id': 1, 'hidden': 1}) \
                         .sort('doc_id', 1) \
                         .to_list()
    exist_pids = [pdoc['doc_id'] for pdoc in pdocs]
    if len(pids) != len(exist_pids):
      for pid in pids:
        if pid not in exist_pids:
          raise error.ProblemNotFoundError(self.domain_id, pid)
    for pdoc in pdocs:
      if pdoc.get('hidden', False):
        self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    await training.edit(self.domain_id, tdoc['doc_id'], title=title, content=content,
                        dag=dag, desc=desc)
    self.json_or_redirect(self.reverse_url('training_detail', tid=tid))
