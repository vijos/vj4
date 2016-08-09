import asyncio
import hmac

from bson import objectid

from vj4 import app
from vj4 import error
from vj4 import template
from vj4.model import builtin
from vj4.model import message
from vj4.model import token
from vj4.model import user
from vj4.service import bus
from vj4.handler import base
from vj4.util import useragent
from vj4.util import validator
from vj4.util import geoip

TOKEN_TYPE_TEXTS = {
  token.TYPE_SAVED_SESSION: 'Saved session',
  token.TYPE_UNSAVED_SESSION: 'Temporary session',
}


@app.route('/home/security', 'home_security')
class HomeSecurityView(base.OperationHandler):
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
      raise error.ChangePasswordError(self.user['_id'])
    self.json_or_redirect(self.referer_or_main)

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


@app.route('/home/account', 'home_account')
class HomeAccountView(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    self.render('home_account.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, gravatar: str, qq: str, gender: int,
                 show_mail: int, show_qq: int, show_gender: int,
                 view_lang: str, code_lang: str, show_tags: int, send_code: int):
    # TODO(twd2): check show_tags
    validator.check_gender(gender)
    validator.check_privacy('show_mail', show_mail)
    validator.check_privacy('show_qq', show_qq)
    validator.check_privacy('show_gender', show_gender)
    validator.check_function('send_code', send_code)
    validator.check_code_lang('code_lang', code_lang)
    validator.check_view_lang(view_lang)
    await user.set_by_uid(self.user['_id'], g=gravatar, qq=qq, gender=gender,
                          show_mail=show_mail, show_qq=show_qq, show_gender=show_gender,
                          view_lang=view_lang, code_lang=code_lang, show_tags=show_tags, send_code=send_code)
    self.json_or_redirect(self.referer_or_main)


@app.route('/home/messages', 'home_messages')
class HomeMessagesView(base.OperationHandler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): projection, pagination.
    messages = await message.get_multi(self.user['_id']).sort([('_id', -1)]).to_list(50)
    await asyncio.gather(user.attach_udocs(messages, 'sender_uid',
                                           'sender_udoc', user.PROJECTION_PUBLIC),
                         user.attach_udocs(messages, 'sendee_uid',
                                           'sendee_udoc', user.PROJECTION_PUBLIC))
    for mdoc in messages:
      mdoc['sender_udoc']['gravatar_url'] = (
        template.gravatar_url(mdoc['sender_udoc']['gravatar'] or None))
      mdoc['sendee_udoc']['gravatar_url'] = (
        template.gravatar_url(mdoc['sendee_udoc']['gravatar'] or None))
    self.json_or_render('home_messages.html', messages=messages)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_send_message(self, *, uid: int, content: str):
    udoc = await user.get_by_uid(uid, user.PROJECTION_PUBLIC)
    if not udoc:
      raise error.UserNotFoundError(uid)
    mdoc = await message.add(self.user['_id'], udoc['_id'], content)
    if self.user['_id'] != uid:
      await bus.publish('message_received-' + str(uid), mdoc)

    # projection
    mdoc['sender_udoc'] = await user.get_by_uid(self.user['_id'], user.PROJECTION_PUBLIC)
    mdoc['sender_udoc']['gravatar_url'] = (
      template.gravatar_url(mdoc['sender_udoc']['gravatar'] or None))
    mdoc['sendee_udoc'] = udoc
    mdoc['sendee_udoc']['gravatar_url'] = (
      template.gravatar_url(mdoc['sendee_udoc']['gravatar'] or None))
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
        sendee_uid = mdoc['sendee_uid']
      else:
        sendee_uid = mdoc['sender_uid']
      await bus.publish('message_received-' + str(sendee_uid), mdoc)
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

