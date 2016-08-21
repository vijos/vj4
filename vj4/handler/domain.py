from vj4 import app
from vj4.model import builtin
from vj4.model import domain
from vj4.model import user
from vj4.handler import base


@app.route('/domain', 'domain_main')
class DomainMainHandler(base.Handler):
  async def get(self):
    self.render('domain_main.html',
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_main'), None)])


@app.route('/domain/edit', 'domain_edit')
class DomainEditHandler(base.Handler):
  @base.require_perm(builtin.PERM_EDIT_DESCRIPTION)
  async def get(self):
    udoc = await user.get_by_uid(self.domain['owner_uid'], user.PROJECTION_PUBLIC)
    self.render('domain_edit.html', udoc=udoc,
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
    udoc = await user.get_by_uid(self.domain['owner_uid'], user.PROJECTION_PUBLIC)
    self.render('domain_edit.html', udoc=udoc,
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_edit'), None)])


@app.route('/domain/user', 'domain_user')
class DomainUserHandler(base.Handler):
  async def get(self):
    self.render('domain_user.html')


@app.route('/domain/role', 'domain_role')
class DomainRoleHandler(base.Handler):
  async def get(self):
    rudocs = dict((role, []) for role in self.domain['roles'])
    uddocs = await domain.get_list_users_by_role(self.domain_id, {'$gt': ''}, {'uid': 1, 'role': 1})
    for uddoc in uddocs:
      if uddoc['role'] in rudocs:
        rudocs[uddoc['role']].append(uddoc)
    self.render('domain_role.html', rudocs=rudocs,
                path_components=[(self.domain_id, self.reverse_url('main')),
                                 (self.translate('domain_role'), None)])
