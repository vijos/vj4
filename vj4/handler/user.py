import asyncio
import datetime

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import domain
from vj4.model import record
from vj4.model import system
from vj4.model import token
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.model.adaptor import problem
from vj4.model.adaptor import setting
from vj4.util import misc
from vj4.util import options
from vj4.util import pagination
from vj4.util import validator
from vj4.handler import base


class UserSettingsMixin(object):
  def can_view(self, udoc, key):
    privacy = udoc.get('show_' + key, next(iter(setting.SETTINGS_BY_KEY['show_' + key].range)))
    return udoc['_id'] == self.user['_id'] \
           or (privacy == constant.setting.PRIVACY_PUBLIC and True) \
           or (privacy == constant.setting.PRIVACY_REGISTERED_ONLY
               and self.has_priv(builtin.PRIV_USER_PROFILE)) \
           or (privacy == constant.setting.PRIVACY_SECRET
               and self.has_priv(builtin.PRIV_VIEW_USER_SECRET))

  def get_udoc_setting(self, udoc, key):
    if self.can_view(udoc, key):
      return udoc.get(key, None)
    else:
      return None


@app.route('/register', 'user_register', global_route=True)
class UserRegisterHandler(base.Handler):
  @base.require_priv(builtin.PRIV_REGISTER_USER)
  async def get(self):
    self.render('user_register.html')

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.post_argument
  @base.sanitize
  @base.limit_rate('send_mail', 3600, 30)
  async def post(self, *, mail: str):
    validator.check_mail(mail)
    if await user.get_by_mail(mail):
      raise error.UserAlreadyExistError(mail)
    rid, _ = await token.add(token.TYPE_REGISTRATION,
                             options.registration_token_expire_seconds,
                             mail=mail)
    await self.send_mail(mail, 'Sign Up', 'user_register_mail.html',
                         url=self.reverse_url('user_register_with_code', code=rid))
    self.render('user_register_mail_sent.html')


@app.route('/register/{code}', 'user_register_with_code', global_route=True)
class UserRegisterWithCodeHandler(base.Handler):
  TITLE = 'user_register'

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.route_argument
  @base.sanitize
  async def get(self, *, code: str):
    doc = await token.get(code, token.TYPE_REGISTRATION)
    if not doc:
      raise error.InvalidTokenError(token.TYPE_REGISTRATION, code)
    self.render('user_register_with_code.html', mail=doc['mail'])

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.route_argument
  @base.post_argument
  @base.sanitize
  async def post(self, *, code: str, uname: str, password: str, verify_password: str):
    doc = await token.get(code, token.TYPE_REGISTRATION)
    if not doc:
      raise error.InvalidTokenError(token.TYPE_REGISTRATION, code)
    if password != verify_password:
      raise error.VerifyPasswordError()
    uid = await system.inc_user_counter()
    await user.add(uid, uname, password, doc['mail'], self.remote_ip)
    await token.delete(code, token.TYPE_REGISTRATION)
    await self.update_session(new_saved=False, uid=uid)
    self.json_or_redirect(self.reverse_url('domain_main'))


@app.route('/lostpass', 'user_lostpass', global_route=True)
class UserLostpassHandler(base.Handler):
  @base.require_priv(builtin.PRIV_REGISTER_USER)
  async def get(self):
    self.render('user_lostpass.html')

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.post_argument
  @base.sanitize
  @base.limit_rate('send_mail', 3600, 30)
  async def post(self, *, mail: str):
    validator.check_mail(mail)
    udoc = await user.get_by_mail(mail)
    if not udoc:
      raise error.UserNotFoundError(mail)
    rid, _ = await token.add(token.TYPE_LOSTPASS,
                             options.lostpass_token_expire_seconds,
                             uid=udoc['_id'])
    await self.send_mail(mail, 'Lost Password', 'user_lostpass_mail.html',
                         url=self.reverse_url('user_lostpass_with_code', code=rid),
                         uname=udoc['uname'])
    self.render('user_lostpass_mail_sent.html')


@app.route('/lostpass/{code}', 'user_lostpass_with_code', global_route=True)
class UserLostpassWithCodeHandler(base.Handler):
  TITLE = 'user_lostpass'

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.route_argument
  @base.sanitize
  async def get(self, *, code: str):
    tdoc = await token.get(code, token.TYPE_LOSTPASS)
    if not tdoc:
      raise error.InvalidTokenError(token.TYPE_LOSTPASS, code)
    udoc = await user.get_by_uid(tdoc['uid'])
    self.render('user_lostpass_with_code.html', uname=udoc['uname'])

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.route_argument
  @base.post_argument
  @base.sanitize
  async def post(self, *, code: str, password: str, verify_password: str):
    tdoc = await token.get(code, token.TYPE_LOSTPASS)
    if not tdoc:
      raise error.InvalidTokenError(token.TYPE_LOSTPASS, code)
    if password != verify_password:
      raise error.VerifyPasswordError()
    await user.set_password(tdoc['uid'], password)
    await token.delete(code, token.TYPE_LOSTPASS)
    self.json_or_redirect(self.reverse_url('domain_main'))


@app.route('/login', 'user_login', global_route=True)
class UserLoginHandler(base.Handler):
  async def get(self):
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      self.redirect(self.reverse_url('domain_main'))
    else:
      self.render('user_login.html')

  @base.post_argument
  @base.sanitize
  async def post(self, *, uname: str, password: str, rememberme: bool=False):
    udoc = await user.check_password_by_uname(uname, password, auto_upgrade=True)
    if not udoc:
      raise error.LoginError(uname)
    await asyncio.gather(user.set_by_uid(udoc['_id'],
                                         loginat=datetime.datetime.utcnow(),
                                         loginip=self.remote_ip),
                         self.update_session(new_saved=rememberme, uid=udoc['_id']))
    self.json_or_redirect(self.referer_or_main)


@app.route('/logout', 'user_logout', global_route=True)
class UserLogoutHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    self.render('user_logout.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  async def post(self):
    await self.delete_session()
    self.json_or_redirect(self.referer_or_main)


@app.route('/user/{uid:-?\d+}', 'user_detail')
class UserDetailHandler(base.Handler, UserSettingsMixin):
  @base.route_argument
  @base.sanitize
  async def get(self, *, uid: int):
    is_self_profile = self.has_priv(builtin.PRIV_USER_PROFILE) and self.user['_id'] == uid
    udoc = await user.get_by_uid(uid)
    if not udoc:
      raise error.UserNotFoundError(uid)
    dudoc, sdoc = await asyncio.gather(domain.get_user(self.domain_id, udoc['_id']),
                                       token.get_most_recent_session_by_uid(udoc['_id']))

    rdocs = record.get_multi(get_hidden=self.has_priv(builtin.PRIV_VIEW_HIDDEN_RECORD),
                             uid=uid).sort([('_id', -1)])
    rdocs = await rdocs.limit(10).to_list()
    pdict = await problem.get_dict_multi_domain((rdoc['domain_id'], rdoc['pid']) for rdoc in rdocs)

    # check hidden problem
    if not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      f = {'hidden': False}
    else:
      f = {}
    pdocs = problem.get_multi(domain_id=self.domain_id, owner_uid=uid, **f).sort([('_id', -1)])
    pcount = await pdocs.count()
    pdocs = await pdocs.limit(10).to_list()

    psdocs = problem.get_multi_solution_by_uid(self.domain_id, uid)
    psdocs_hot = problem.get_multi_solution_by_uid(self.domain_id, uid)
    pscount = await psdocs.count()
    psdocs = await psdocs.limit(10).to_list()
    psdocs_hot = await psdocs_hot.sort([('vote', -1), ('doc_id', -1)]).limit(10).to_list()

    if self.has_perm(builtin.PERM_VIEW_DISCUSSION):
      ddocs = discussion.get_multi(self.domain_id, owner_uid=uid)
      dcount = await ddocs.count()
      ddocs = await ddocs.limit(10).to_list()
      vndict = await discussion.get_dict_vnodes(self.domain_id, map(discussion.node_id, ddocs))
    else:
      ddocs = []
      vndict = {}
      dcount = 0

    self.render('user_detail.html', is_self_profile=is_self_profile,
                udoc=udoc, dudoc=dudoc, sdoc=sdoc,
                rdocs=rdocs, pdict=pdict, pdocs=pdocs, pcount=pcount,
                psdocs=psdocs, pscount=pscount, psdocs_hot=psdocs_hot,
                ddocs=ddocs, dcount=dcount, vndict=vndict)


@app.route('/user/search', 'user_search')
class UserSearchHandler(base.Handler):
  def modify_udoc(self, udict, key):
    udoc = udict[key]
    gravatar_url = misc.gravatar_url(udoc.get('gravatar'))
    if 'gravatar' in udoc and udoc['gravatar']:
      udict[key] = {**udoc,
                    'gravatar_url': gravatar_url,
                    'gravatar': ''}

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, q: str, exact_match: bool=False):
    if exact_match:
      udocs = []
    else:
      udocs = await user.get_prefix_list(q, user.PROJECTION_PUBLIC, 20)
    try:
      udoc = await user.get_by_uid(int(q), user.PROJECTION_PUBLIC)
      if udoc:
        udocs.insert(0, udoc)
    except ValueError as e:
      pass
    for i in range(len(udocs)):
      self.modify_udoc(udocs, i)
    self.json(udocs)
