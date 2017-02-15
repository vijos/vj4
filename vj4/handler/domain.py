import asyncio
import collections

from vj4 import app
from vj4 import error
from vj4.model import builtin
from vj4.model import domain
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.model.adaptor import contest
from vj4.model.adaptor import training
from vj4.handler import base
import vj4.handler.training

@app.route('/', 'domain_main')
class DomainMainHandler(base.Handler, vj4.handler.training.TrainingMixin):
  CONTESTS_ON_MAIN = 5
  TRAININGS_ON_MAIN = 5
  DISCUSSIONS_ON_MAIN = 20

  async def prepare_contest(self):
    if self.has_perm(builtin.PERM_VIEW_CONTEST):
      tdocs = await contest.get_multi(self.domain_id).to_list(self.CONTESTS_ON_MAIN)
      tsdict = await contest.get_dict_status(self.domain_id, self.user['_id'],
                                             (tdoc['doc_id'] for tdoc in tdocs))
    else:
      tdocs = {}
      tsdict = {}
    return tdocs, tsdict

  async def prepare_training(self):
    if self.has_perm(builtin.PERM_VIEW_TRAINING):
      tdocs = await training.get_multi(self.domain_id).to_list(self.TRAININGS_ON_MAIN)
      tsdict = await training.get_dict_status(self.domain_id, self.user['_id'],
                                             (tdoc['doc_id'] for tdoc in tdocs))
    else:
      tdocs = {}
      tsdict = {}
    return tdocs, tsdict

  async def prepare_discussion(self):
    if self.has_perm(builtin.PERM_VIEW_DISCUSSION):
      ddocs = await discussion.get_multi(self.domain_id).to_list(self.DISCUSSIONS_ON_MAIN)
      vndict = await discussion.get_dict_vnodes(self.domain_id, map(discussion.node_id, ddocs))
    else:
      ddocs = {}
      vndict = {}
    return ddocs, vndict

  async def get(self):
    (tdocs, tsdict), (trdocs, trsdict), (ddocs, vndict) = await asyncio.gather(
      self.prepare_contest(), self.prepare_training(), self.prepare_discussion())
    uids = set()
    uids.update(ddoc['owner_uid'] for ddoc in ddocs)
    udict = await user.get_dict(uids)
    self.render('domain_main.html', discussion_nodes=await discussion.get_nodes(self.domain_id),
                tdocs=tdocs, tsdict=tsdict, trdocs=trdocs, trsdict=trsdict,
                ddocs=ddocs, vndict=vndict,
                udict=udict, datetime_stamp=self.datetime_stamp)


@app.route('/manage', 'domain_manage')
class DomainManageHandler(base.Handler):
  async def get(self):
    if not self.has_perm(builtin.PERM_EDIT_PERM):
       self.check_perm(builtin.PERM_EDIT_DESCRIPTION)
    self.render('domain_manage.html', owner_udoc=await user.get_by_uid(self.domain['owner_uid']))


@app.route('/domain/edit', 'domain_manage_edit')
class DomainEditHandler(base.Handler):
  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  async def get(self):
    self.render('domain_manage_edit.html')

  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, name: str, gravatar: str):
    await domain.edit(self.domain_id, name=name, gravatar=gravatar)
    self.json_or_redirect(self.url)


@app.route('/domain/user', 'domain_manage_user')
class DomainUserHandler(base.OperationHandler):
  @base.require_perm(builtin.PERM_EDIT_PERM)
  async def get(self):
    uids = [self.domain['owner_uid']]
    rudocs = collections.defaultdict(list)
    async for dudoc in domain.get_multi_user(domain_id=self.domain_id,
                                             role={'$gte': ''},
                                             fields={'uid': 1, 'role': 1}):
      if 'role' in dudoc:
        uids.append(dudoc['uid'])
        rudocs[dudoc['role']].append(dudoc)
    roles = sorted(list(self.domain['roles'].keys()))
    roles_with_text = [(role, role) for role in roles]
    udict = await user.get_dict(uids)
    self.render('domain_manage_user.html', roles=roles, roles_with_text=roles_with_text,
                rudocs=rudocs, udict=udict)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_set_user(self, *, uid: int, role: str):
    if role:
      await domain.set_user_role(self.domain_id, uid, role)
    else:
      await domain.unset_user_role(self.domain_id, uid)
    self.json_or_redirect(self.url)


  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_set_users(self, *, uid: int, role: str):
    try:
      uids = map(int, self.request.POST.getall('uid'))
    except ValueError:
      raise error.ValidationError('uid')
    if role:
      # user must exist.
      await domain.set_users_role(self.domain_id, uids, role)
    else:
      await domain.unset_users_role(self.domain_id, uids)
    self.json_or_redirect(self.url)


@app.route('/domain/permission', 'domain_manage_permission')
class DomainPermissionHandler(base.Handler):
  @base.require_perm(builtin.PERM_EDIT_PERM)
  async def get(self):
    def bitand(a, b):
      return a & b
    roles = sorted(list(self.domain['roles'].keys()))
    self.render('domain_manage_permission.html', bitand=bitand, roles=roles)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.post_argument
  @base.require_csrf_token
  async def post(self, **kwargs):
    new_roles = dict()
    for role in self.domain['roles']:
      perms = 0
      for perm in self.request.POST.getall(role, []):
       perm = int(perm)
       if perm in builtin.PERMS_BY_KEY:
          perms |= perm
      new_roles[role] = perms
    await domain.edit(self.domain_id, roles=new_roles)
    self.json_or_redirect(self.url)


@app.route('/domain/role', 'domain_manage_role')
class DomainRoleHandler(base.OperationHandler):
  @base.require_perm(builtin.PERM_EDIT_PERM)
  async def get(self):
    rucounts = collections.defaultdict(int)
    async for dudoc in domain.get_multi_user(domain_id=self.domain_id,
                                             role={'$gte': ''},
                                             fields={'uid': 1, 'role': 1}):
      if 'role' in dudoc:
        rucounts[dudoc['role']] += 1
    roles = sorted(list(self.domain['roles'].keys()))
    self.render('domain_manage_role.html', rucounts=rucounts, roles=roles)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_set(self, *, role: str, perm: int=builtin.DEFAULT_PERMISSIONS):
    await domain.set_role(self.domain_id, role, perm)
    self.json_or_redirect(self.url)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_delete(self, *, role: str):
    await domain.delete_roles(self.domain_id, self.request.POST.getall('role'))
    self.json_or_redirect(self.url)
