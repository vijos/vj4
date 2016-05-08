import hmac
from bson import objectid
from vj4 import app
from vj4 import error
from vj4.model import builtin
from vj4.model import message
from vj4.model import token
from vj4.model import user
from vj4.view import base

TOKEN_TYPE_TEXTS = {
  token.TYPE_SAVED_SESSION: 'Saved session',
  token.TYPE_UNSAVED_SESSION: 'Unsaved session',
}

@app.route('/home/security', 'home_security')
class HomeSecurityView(base.OperationView):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): pagination? or limit session count for uid?
    sessions = await token.get_session_list_by_uid(self.user['_id'])
    for session in sessions:
      session['token_digest'] = hmac.new(b'token_digest', session['_id'], 'sha256').hexdigest()
      session['is_current'] = (session['_id'] == self.session['_id'])
    self.render('home_security.html', sessions=sessions)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_change_password(self, *, current_password, new_password, verify_password):
    if new_password != verify_password:
      raise error.VerifyPasswordError()
    doc = await user.change_password(self.user['_id'], current_password, new_password)
    if not doc:
      raise error.ChangePasswordError(self.user['_id'])
    self.json_or_redirect(self.referer_or_main)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_delete_token(self, *, token_type, token_digest):
    sessions = await token.get_session_list_by_uid(self.user['_id'])
    for session in sessions:
      if (int(token_type) == session['token_type'] and
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
class HomeAccountView(base.View):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    self.render('home_account.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.post_argument
  @base.require_csrf_token
  async def post(self, *, gravatar, qq, gender, signature):
    # TODO(twd2): check gender
    await user.set_by_uid(self.user['_id'], g=gravatar, qq=qq, gender=gender, sig=signature)
    self.json_or_redirect(self.referer_or_main)

@app.route('/home/messages', 'home_messages')
class HomeMessagesView(base.OperationView):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  async def get(self):
    # TODO(iceboy): projection, pagination.
    messages = await message.get_multi(self.user['_id']).sort([('_id', -1)]).to_list(50)
    self.render('home_messages.html', messages=messages)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_send_message(self, *, uid, content):
    # TODO(iceboy): int by annotation?
    uid = int(uid)
    udoc = await user.get_by_uid(uid)
    if not udoc:
      raise error.UserNotFoundError(uid)
    await message.add(self.user['_id'], udoc['_id'], content)
    self.json_or_redirect(self.referer_or_main)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_reply_message(self, *, message_id, content):
    mdoc = await message.add_reply(objectid.ObjectId(message_id), self.user['_id'], content)
    if not mdoc:
      return error.MessageNotFoundError(message_id)
    # TODO(iceboy): Fill in JSON result.
    self.json_or_redirect(self.referer_or_main)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  async def post_delete_message(self, *, message_id):
    await message.delete(objectid.ObjectId(message_id), self.user['_id'])
    self.json_or_redirect(self.referer_or_main)
