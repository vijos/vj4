import asyncio
import hmac
import itertools

from bson import objectid

from vj4 import app
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.model import message
from vj4.model import token
from vj4.model import user
from vj4.model.adaptor import setting
from vj4.model.adaptor import userfile
from vj4.handler import base
from vj4.service import bus
from vj4.util import useragent
from vj4.util import geoip
from vj4.util import misc
from vj4.util import options
from vj4.util import validator


TOKEN_TYPE_TEXTS = {
  token.TYPE_SAVED_SESSION: 'Saved session',
  token.TYPE_UNSAVED_SESSION: 'Temporary session',
}


@app.route('/home/security', 'home_security', global_route=True)
class HomeSecurityHandler(base.OperationHandler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): pagination? or limit session count for uid?
    sessions = await token.get_session_list_by_uid(self.user['_id'])
    annotated_sessions = list({
        **session,
        'update_ua': useragent.parse(session.get('update_ua') or
                                     session.get('create_ua') or ''),
        'update_geoip': geoip.ip2geo(session.get('update_ip') or
                                     session.get('create_ip'),
                                     self.get_setting('view_lang')),
        'token_digest': hmac.new(b'token_digest', session['_id'], 'sha256').hexdigest(),
        'is_current': session['_id'] == self.session['_id']
    } for session in sessions)
    self.render('home_security.html', sessions=annotated_sessions)

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
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  @base.limit_rate('send_mail', 3600, 50)
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
                             options.changemail_token_expire_seconds,
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
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_delete_all_tokens(self):
    await token.delete_by_uid(self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/home/security/changemail/{code}', 'user_changemail_with_code', global_route=True)
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


@app.route('/home/account', 'home_account', global_route=True)
class HomeAccountHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    self.render('home_settings.html', category='account', settings=setting.ACCOUNT_SETTINGS)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  async def post(self, **kwargs):
    await self.set_settings(**kwargs)
    self.json_or_redirect(self.url)


@app.route('/home/preference', 'home_preference', global_route=True)
class HomeAccountHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    self.render('home_settings.html', category='preference', settings=setting.PREFERENCE_SETTINGS)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  async def post(self, **kwargs):
    await self.set_settings(**kwargs)
    self.json_or_redirect(self.url)


@app.route('/home/messages', 'home_messages', global_route=True)
class HomeMessagesHandler(base.OperationHandler):
  def modify_udoc(self, udict, key):
    udoc = udict.get(key)
    if not udoc:
      return
    gravatar_url = misc.gravatar_url(udoc.get('gravatar'))
    if 'gravatar' in udoc and udoc['gravatar']:
      udict[key] = {**udoc,
                    'gravatar_url': gravatar_url,
                    'gravatar': ''}

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): projection, pagination.
    mdocs = await message.get_multi(self.user['_id']).sort([('_id', -1)]).limit(50).to_list()
    udict = await user.get_dict(
        itertools.chain.from_iterable((mdoc['sender_uid'], mdoc['sendee_uid']) for mdoc in mdocs),
        fields=user.PROJECTION_PUBLIC)
    # TODO(twd2): improve here:
    for mdoc in mdocs:
      self.modify_udoc(udict, mdoc['sender_uid'])
      self.modify_udoc(udict, mdoc['sendee_uid'])
    self.json_or_render('home_messages.html', messages=mdocs, udict=udict)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_send_message(self, *, uid: int, content: str):
    udoc = await user.get_by_uid(uid, user.PROJECTION_PUBLIC)
    if not udoc:
      raise error.UserNotFoundError(uid)
    mdoc = await message.add(self.user['_id'], udoc['_id'], content)
    # TODO(twd2): improve here:
    # projection
    sender_udoc = await user.get_by_uid(self.user['_id'], user.PROJECTION_PUBLIC)
    mdoc['sender_udoc'] = sender_udoc
    self.modify_udoc(mdoc, 'sender_udoc')
    mdoc['sendee_udoc'] = udoc
    self.modify_udoc(mdoc, 'sendee_udoc')
    if self.user['_id'] != uid:
      await bus.publish('message_received-' + str(uid), {'type': 'new', 'data': mdoc})
    self.json_or_redirect(self.url, mdoc=mdoc)

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
    self.json_or_redirect(self.url, reply=reply)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_message(self, *, message_id: objectid.ObjectId):
    await message.delete(message_id, self.user['_id'])
    self.json_or_redirect(self.url)


@app.connection_route('/home/messages-conn', 'home_messages-conn', global_route=True)
class HomeMessagesConnection(base.Connection):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def on_open(self):
    await super(HomeMessagesConnection, self).on_open()
    bus.subscribe(self.on_message_received, ['message_received-' + str(self.user['_id'])])

  async def on_message_received(self, e):
    self.send(**e['value'])

  async def on_close(self):
    bus.unsubscribe(self.on_message_received)


@app.route('/home/domain', 'home_domain', global_route=True)
class HomeDomainHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    pending_ddocs = await domain.get_pending(owner_uid=self.user['_id']) \
                                .to_list()
    dudict = await domain.get_dict_user_by_domain_id(self.user['_id'])
    dids = list(dudict.keys())
    ddocs = await domain.get_multi(_id={'$in': dids}) \
                        .to_list()
    can_manage = {}
    for ddoc in builtin.DOMAINS + ddocs:
      role = dudict.get(ddoc['_id'], {}).get('role', builtin.ROLE_DEFAULT)
      mask = domain.get_all_roles(ddoc).get(role, builtin.PERM_NONE)
      can_manage[ddoc['_id']] = (
          ((builtin.PERM_EDIT_DESCRIPTION | builtin.PERM_EDIT_PERM) & mask) != 0
          or self.has_priv(builtin.PRIV_MANAGE_ALL_DOMAIN))
    self.render('home_domain.html', pending_ddocs=pending_ddocs, ddocs=ddocs, dudict=dudict, can_manage=can_manage)

  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, domain_id: str):
    await domain.add_continue(domain_id, self.user['_id'])
    self.json_or_redirect(self.url)


@app.route('/home/domain/create', 'home_domain_create', global_route=True)
class HomeDomainCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_CREATE_DOMAIN)
  async def get(self):
    self.render('home_domain_create.html')

  @base.require_priv(builtin.PRIV_CREATE_DOMAIN)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, id: str, name: str, gravatar: str, bulletin: str):
    domain_id = await domain.add(id, self.user['_id'], name=name,
                                 gravatar=gravatar, bulletin=bulletin)
    self.json_or_redirect(self.reverse_url('domain_manage', domain_id=domain_id))


@app.route('/home/file', 'home_file', global_route=True)
class HomeFileHandler(base.OperationHandler):
  def file_url(self, fdoc):
    return options.cdn_prefix.rstrip('/') + \
      self.reverse_url('fs_get', domain_id=builtin.DOMAIN_ID_SYSTEM,
                       secret=fdoc['metadata']['secret'])

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    ufdocs = await userfile.get_multi(owner_uid=self.user['_id']).to_list()
    fdict = await fs.get_meta_dict(ufdoc.get('file_id') for ufdoc in ufdocs)
    self.render('home_file.html', ufdocs=ufdocs, fdict=fdict)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_delete(self, *, ufid: document.convert_doc_id):
    ufdoc = await userfile.get(ufid)
    if not self.own(ufdoc, priv=builtin.PRIV_DELETE_FILE_SELF):
      self.check_priv(builtin.PRIV_DELETE_FILE)
    result = await userfile.delete(ufdoc['doc_id'])
    if result:
      await userfile.dec_usage(self.user['_id'], ufdoc['length'])
    self.redirect(self.referer_or_main)
