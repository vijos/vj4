from vj4 import app
from vj4.model import builtin
from vj4.model import domain
from vj4.handler import base


@app.route('/domain', 'domain_main')
class DomainMainHandler(base.Handler):
  async def get(self):
    self.render('domain_main.html',
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_main'), None)])


@app.route('/domain/create', 'domain_create')
class DomainCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_CREATE_DOMAIN)
  async def get(self):
    self.render('domain_edit.html',
                path_components=[(self.translate('domain_create'), None)])

  @base.require_priv(builtin.PRIV_CREATE_DOMAIN)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, id: str, description: str):
    domain_id = await domain.add(id, self.user['_id'], description)
    self.json_or_redirect(base._reverse_url('main', domain_id=domain_id))


@app.route('/domain/edit', 'domain_edit')
class DomainEditHandler(base.Handler):
  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  async def get(self):
    self.render('domain_edit.html',
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_edit'), None)])

  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, description: str):
    ddoc = await domain.set(self.domain_id, description=description)
    if ddoc:
      self.domain = ddoc
    self.render('domain_edit.html',
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_edit'), None)])


@app.route('/domain/role', 'domain_role')
class DomainRoleHandler(base.Handler):
  async def get(self):
    self.render('domain_role.html',
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_role'), None)])
