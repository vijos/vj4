import collections

from vj4 import app
from vj4.model import builtin
from vj4.model import domain
from vj4.model.adaptor import discussion
from vj4.handler import base


@app.route('/', 'domain_main')
class DomainMainHandler(base.Handler):
  async def get(self):
    self.render('domain_main.html', discussion_nodes=await discussion.get_nodes(self.domain_id))


@app.route('/manage', 'domain_manage')
class DomainMainHandler(base.Handler):
  async def get(self):
    self.render('domain_manage.html')


@app.route('/domain/edit', 'domain_edit')
class DomainEditHandler(base.Handler):
  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  async def get(self):
    self.render('domain_edit.html')

  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, name: str, gravatar: str):
    ddoc = await domain.edit(self.domain_id, name=name, gravatar=gravatar)
    # TODO(iceboy): FIXME!!! THIS IS A DISASTER!!!
    if ddoc:
      self.domain = ddoc
    self.render('domain_edit.html')


@app.route('/domain/user', 'domain_user')
class DomainUserHandler(base.Handler):
  async def get(self):
    self.render('domain_user.html')


@app.route('/domain/permission', 'domain_permission')
class DomainPermissionHandler(base.Handler):
  async def get(self):
    self.render('domain_permission.html')


@app.route('/domain/role', 'domain_role')
class DomainRoleHandler(base.OperationHandler):
  async def get(self):
    rudocs = collections.defaultdict(list)
    async for uddoc in domain.get_multi_user(domain_id=self.domain_id,
                                             fields={'uid': 1, 'role': 1}):
      if 'role' in uddoc:
        rudocs[uddoc['role']].append(uddoc)
    self.render('domain_role.html', rudocs=rudocs)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_set(self, *, role: str, perm: int):
    await domain.set_role(self.domain_id, role, perm)
    self.json_or_redirect(self.referer_or_main)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_delete(self, *, role: str, perm: int=None):
    await domain.delete_role(self.domain_id, role)
    self.json_or_redirect(self.referer_or_main)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_set_user(self, *, uid: int, role: str):
    await domain.set_user_role(self.domain_id, uid, role)
    self.json_or_redirect(self.referer_or_main)

  @base.require_perm(builtin.PERM_EDIT_PERM)
  @base.require_csrf_token
  @base.sanitize
  async def post_unset_user(self, *, uid: int):
    await domain.unset_user_role(self.domain_id, uid)
    self.json_or_redirect(self.referer_or_main)
