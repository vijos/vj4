import asyncio
import hmac

from bson import objectid

from vj4 import app
from vj4 import error
from vj4 import template
from vj4.model import builtin
from vj4.model import domain
from vj4.model import message
from vj4.model import token
from vj4.model import user
from vj4.handler import base
from vj4.service import bus
from vj4.util import useragent
from vj4.util import geoip
from vj4.util import options
from vj4.util import validator


TOKEN_TYPE_TEXTS = {
  token.TYPE_SAVED_SESSION: 'Saved session',
  token.TYPE_UNSAVED_SESSION: 'Temporary session',
}


@app.route('/home/security', 'home_security')
class HomeSecurityHandler(base.OperationHandler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): pagination? or limit session count for uid?
    sessions = await token.get_session_list_by_uid(self.user['_id'])
    for session in sessions:
      session['update_ua'] = useragent.parse(session['update_ua'])
      session['update_geoip'] = geoip.ip2geo(session['update_ip'], self.get_setting('view_lang'))
      session['token_digest'] = hmac.new(b'token_digest', session['_id'], 'sha256').hexdigest()
      session['is_current'] = (session['_id'] == self.session['_id'])
    self.render('home_security.html', sessions=sessions)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_change_password(self, *,
                                 current_password: str,
                                 new_password: str,
                                 verify_password: str):
    if new_password != verify_password:
      raise error.VerifyPasswordError()
    doc = await user.change_password(self.user['_id'], current_password, new_password)
    if not doc:
      raise error.CurrentPasswordError(self.user['_id'])
    self.json_or_redirect(self.referer_or_main)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_change_mail(self, *, current_password: str, mail: str):
    validator.check_mail(mail)
    udoc, mail_holder_udoc = await asyncio.gather(
      user.check_password_by_uid(self.user['_id'], current_password),
      user.get_by_mail(mail))
    # TODO(twd2): raise other errors.
    if not udoc:
      raise error.CurrentPasswordError(self.user['uname'])
    if mail_holder_udoc:
      raise error.UserAlreadyExistError(mail)
    rid, _ = await token.add(token.TYPE_CHANGEMAIL,
                             options.options.changemail_token_expire_seconds,
                             uid=udoc['_id'], mail=mail)
    await self.send_mail(mail, 'Change Email', 'user_changemail_mail.html',
                         url=self.reverse_url('user_changemail_with_code', code=rid),
                         uname=udoc['uname'])
    self.render('user_changemail_mail_sent.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_token(self, *, token_type: int, token_digest: str):
    sessions = await token.get_session_list_by_uid(self.user['_id'])
    for session in sessions:
      if (token_type == session['token_type'] and
              token_digest == hmac.new(b'token_digest', session['_id'], 'sha256').hexdigest()):
        await token.delete_by_hashed_id(session['_id'], session['token_type'])
        break
    else:
      raise error.InvalidTokenDigestError(token_type, token_digest)
    self.json_or_redirect(self.referer_or_main)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_delete_all_tokens(self):
    await token.delete_by_uid(self.user['_id'])
    self.json_or_redirect(self.referer_or_main)


@app.route('/home/security/changemail/{code}', 'user_changemail_with_code')
class UserChangemailWithCodeHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.sanitize
  async def get(self, *, code: str):
    tdoc = await token.get(code, token.TYPE_CHANGEMAIL)
    if not tdoc or tdoc['uid'] != self.user['_id']:
      raise error.InvalidTokenError(token.TYPE_CHANGEMAIL, code)
    mail_holder_udoc = await user.get_by_mail(tdoc['mail'])
    if mail_holder_udoc:
      raise error.UserAlreadyExistError(tdoc['mail'])
    # TODO(twd2): Ensure mail is unique.
    await user.set_mail(self.user['_id'], tdoc['mail'])
    await token.delete(code, token.TYPE_CHANGEMAIL)
    self.json_or_redirect(self.reverse_url('home_security'))


@app.route('/home/account', 'home_account')
class HomeAccountHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    self.render('home_account.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  async def post(self, **kwargs):
    await self.set_settings(**kwargs)
    self.json_or_redirect(self.referer_or_main)


@app.route('/home/messages', 'home_messages')
class HomeMessagesHandler(base.OperationHandler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): projection, pagination.
    mdocs = await message.get_multi(self.user['_id']).sort([('_id', -1)]).to_list(50)
    await asyncio.gather(
      user.attach_udocs(mdocs, 'sender_uid', 'sender_udoc', user.PROJECTION_PUBLIC),
      user.attach_udocs(mdocs, 'sendee_uid', 'sendee_udoc', user.PROJECTION_PUBLIC))
    # TODO(twd2): improve here:
    for mdoc in mdocs:
      if 'gravatar' in mdoc['sender_udoc']:
        mdoc['sender_udoc']['gravatar_url'] = (
          template.gravatar_url(mdoc['sender_udoc'].pop('gravatar')))
      if 'gravatar' in mdoc['sendee_udoc']:
        mdoc['sendee_udoc']['gravatar_url'] = (
          template.gravatar_url(mdoc['sendee_udoc'].pop('gravatar')))
    self.json_or_render('home_messages.html', messages=mdocs)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_send_message(self, *, uid: int, content: str):
    udoc = await user.get_by_uid(uid, user.PROJECTION_PUBLIC)
    if not udoc:
      raise error.UserNotFoundError(uid)
    mdoc = await message.add(self.user['_id'], udoc['_id'], content)
    # projection
    mdoc['sender_udoc'] = await user.get_by_uid(self.user['_id'], user.PROJECTION_PUBLIC)
    # TODO(twd2): improve here:
    mdoc['sender_udoc']['gravatar_url'] = (
      template.gravatar_url(mdoc['sender_udoc'].pop('gravatar')))
    mdoc['sendee_udoc'] = udoc
    # TODO(twd2): improve here:
    mdoc['sendee_udoc']['gravatar_url'] = (
      template.gravatar_url(mdoc['sendee_udoc'].pop('gravatar')))
    if self.user['_id'] != uid:
      await bus.publish('message_received-' + str(uid), {'type': 'new', 'data': mdoc})
    self.json_or_redirect(self.referer_or_main, mdoc=mdoc)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_reply_message(self, *, message_id: objectid.ObjectId, content: str):
    mdoc, reply = await message.add_reply(message_id, self.user['_id'], content)
    if not mdoc:
      return error.MessageNotFoundError(message_id)
    if mdoc['sender_uid'] != mdoc['sendee_uid']:
      if mdoc['sender_uid'] == self.user['_id']:
        other_uid = mdoc['sendee_uid']
      else:
        other_uid = mdoc['sender_uid']
      mdoc['reply'] = [reply]
      await bus.publish('message_received-' + str(other_uid), {'type': 'reply', 'data': mdoc})
    self.json_or_redirect(self.referer_or_main, reply=reply)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_message(self, *, message_id: objectid.ObjectId):
    await message.delete(message_id, self.user['_id'])
    self.json_or_redirect(self.referer_or_main)


@app.connection_route('/home/messages-conn', 'home_messages-conn')
class HomeMessagesConnection(base.Connection):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def on_open(self):
    await super(HomeMessagesConnection, self).on_open()
    bus.subscribe(self.on_message_received, ['message_received-' + str(self.user['_id'])])

  async def on_message_received(self, e):
    self.send(**e['value'])

  async def on_close(self):
    bus.unsubscribe(self.on_message_received)


@app.route('/home/domain', 'home_domain')
class HomeDomainHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    uddict = await domain.get_dict_users(self.user['_id'])
    dids = list(uddict.keys())
    ddocs = await domain.get_multi(**{'$or': [{'_id': {'$in': dids}},
                                              {'owner_uid': self.user['_id']}]}) \
                        .to_list(None)
    self.render('home_domain.html', ddocs=ddocs, uddict=uddict)


@app.route('/home/domain/create', 'home_domain_create')
class HomeDomainCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_CREATE_DOMAIN)
  async def get(self):
    self.render('home_domain_create.html')

  @base.require_priv(builtin.PRIV_CREATE_DOMAIN)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, id: str, name: str, gravatar: str):
    domain_id = await domain.add(id, self.user['_id'], name=name, gravatar=gravatar)
    self.json_or_redirect(self.reverse_url('main', domain_id=domain_id))
