import asyncio
import datetime

from vj4 import app
from vj4 import error
from vj4 import template
from vj4.model import builtin
from vj4.model import domain
from vj4.model import system
from vj4.model import token
from vj4.model import user
from vj4.util import options
from vj4.util import validator
from vj4.handler import base


@app.route('/register', 'user_register')
class UserRegisterHandler(base.Handler):
  @base.require_priv(builtin.PRIV_REGISTER_USER)
  async def get(self):
    self.render('user_register.html')

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.limit_rate('user_register', 3600, 60)
  @base.post_argument
  @base.sanitize
  async def post(self, *, mail: str):
    validator.check_mail(mail)
    if await user.get_by_mail(mail):
      raise error.UserAlreadyExistError(mail)
    rid, _ = await token.add(token.TYPE_REGISTRATION,
                             options.options.registration_token_expire_seconds,
                             mail=mail)
    await self.send_mail(mail, 'Sign Up', 'user_register_mail.html',
                         url=self.reverse_url('user_register_with_code', code=rid))
    self.render('user_register_mail_sent.html')


@app.route('/register/{code}', 'user_register_with_code')
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
    self.json_or_redirect(self.reverse_url('main'))


@app.route('/lostpass', 'user_lostpass')
class UserLostpassHandler(base.Handler):
  @base.require_priv(builtin.PRIV_REGISTER_USER)
  async def get(self):
    self.render('user_lostpass.html')

  @base.require_priv(builtin.PRIV_REGISTER_USER)
  @base.limit_rate('user_register', 3600, 60)
  @base.post_argument
  @base.sanitize
  async def post(self, *, mail: str):
    validator.check_mail(mail)
    udoc = await user.get_by_mail(mail)
    if not udoc:
      raise error.UserNotFoundError(mail)
    rid, _ = await token.add(token.TYPE_LOSTPASS,
                             options.options.lostpass_token_expire_seconds,
                             uid=udoc['_id'])
    await self.send_mail(mail, 'Lost Password', 'user_lostpass_mail.html',
                         url=self.reverse_url('user_lostpass_with_code', code=rid),
                         uname=udoc['uname'])
    self.render('user_lostpass_mail_sent.html')


@app.route('/lostpass/{code}', 'user_lostpass_with_code')
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
    self.json_or_redirect(self.reverse_url('main'))


@app.route('/login', 'user_login')
class UserLoginHandler(base.Handler):
  async def get(self):
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      self.redirect(self.reverse_url('main'))
    else:
      self.render('user_login.html')

  @base.post_argument
  @base.sanitize
  async def post(self, *, uname: str, password: str, rememberme: bool=False):
    udoc = await user.check_password_by_uname(uname, password)
    if not udoc:
      raise error.LoginError(uname)
    await asyncio.gather(user.set_by_uid(udoc['_id'],
                                         loginat=datetime.datetime.utcnow(),
                                         loginip=self.remote_ip),
                         self.update_session(new_saved=rememberme, uid=udoc['_id']))
    self.json_or_redirect(self.referer_or_main)


@app.route('/logout', 'user_logout')
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
class UserDetailHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, uid: int):
    udoc = await user.get_by_uid(uid)
    if not udoc:
      raise error.UserNotFoundError(uid)
    dudoc, sdoc = await asyncio.gather(domain.get_user(self.domain_user, udoc),
                                       token.get_most_recent_session_by_uid(udoc['_id']))
    self.render('user_detail.html', udoc=udoc, dudoc=dudoc, sdoc=sdoc)


@app.route('/user/search', 'user_search')
class UserSearchHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, q: str):
    udocs = await user.get_prefix_list(q, user.PROJECTION_PUBLIC, 20)
    try:
      udoc = await user.get_by_uid(int(q), user.PROJECTION_PUBLIC)
      if udoc:
        udocs.insert(0, udoc)
    except ValueError as e:
      pass
    for udoc in udocs:
      if 'gravatar' in udoc:
        udoc['gravatar_url'] = template.gravatar_url(udoc.pop('gravatar'))
    self.json(udocs)
