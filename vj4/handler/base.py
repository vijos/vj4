import accept
import asyncio
import calendar
import functools
import hmac
import logging
import markupsafe
import pytz
import sockjs
from aiohttp import web
from email import utils

from vj4 import app
from vj4 import error
from vj4 import template
from vj4.model import builtin
from vj4.model import domain
from vj4.model import opcount
from vj4.model import token
from vj4.model import user
from vj4.model.adaptor import setting
from vj4.service import mailer
from vj4.util import json
from vj4.util import locale
from vj4.util import options

_logger = logging.getLogger(__name__)


class HandlerBase(setting.SettingMixin):
  NAME = None
  TITLE = None

  async def prepare(self):
    self.session = await self.update_session()
    self.domain_id = self.request.match_info.pop('domain_id', builtin.DOMAIN_ID_SYSTEM)
    if 'uid' in self.session:
      uid = self.session['uid']
      self.user, self.domain, self.domain_user = await asyncio.gather(
          user.get_by_uid(uid), domain.get(self.domain_id), domain.get_user(self.domain_id, uid))
      if not self.user:
        raise error.UserNotFoundError(uid)
      if not self.domain_user:
        self.domain_user = {}
    else:
      self.user = builtin.USER_GUEST
      self.domain = await domain.get(self.domain_id)
      self.domain_user = builtin.DOMAIN_USER_GUEST
    if not self.domain:
      raise error.DomainNotFoundError(self.domain_id)
    self.view_lang = self.get_setting('view_lang')
    # TODO(iceboy): UnknownTimeZoneError
    self.timezone = pytz.timezone(self.get_setting('timezone'))
    self.translate = locale.get_translate(self.view_lang)
    self.datetime_span = functools.partial(_datetime_span, timezone=self.timezone)
    self.datetime_stamp = _datetime_stamp
    self.reverse_url = functools.partial(_reverse_url, domain_id=self.domain_id)
    self.build_path = functools.partial(_build_path, domain_id=self.domain_id,
                                        domain_name=self.domain['name'])
    if not self.has_priv(builtin.PRIV_VIEW_ALL_DOMAIN):
      self.check_perm(builtin.PERM_VIEW)

  def has_perm(self, perm):
    role = self.domain_user.get('role', builtin.ROLE_DEFAULT)
    mask = self.domain['roles'].get(role, builtin.PERM_NONE)
    return ((perm & mask) == perm
            or self.domain['owner_uid'] == self.user['_id']
            or self.has_priv(builtin.PRIV_MANAGE_ALL_DOMAIN))

  def check_perm(self, perm):
    if not self.has_perm(perm):
      raise error.PermissionError(perm)

  def has_priv(self, priv):
    return (priv & self.user['priv']) == priv

  def check_priv(self, priv):
    if not self.has_priv(priv):
      raise error.PrivilegeError(priv)

  def dudoc_has_perm(self, udoc, dudoc, perm):
    if not udoc or not dudoc:
      return False
    # TODO(iceboy): Fix caller when dudoc=None is passed in.
    role = dudoc.get('role', builtin.ROLE_DEFAULT)
    mask = self.domain['roles'].get(role, builtin.PERM_NONE)
    return ((perm & mask) == perm
            or self.domain['owner_uid'] == udoc['_id']
            or self.udoc_has_priv(udoc, builtin.PRIV_MANAGE_ALL_DOMAIN))

  def udoc_has_priv(self, udoc, priv):
    if not udoc:
      return False
    # TODO(iceboy): Fix caller when udoc=None is passed in.
    return (priv & udoc['priv']) == priv

  def own(self, doc, perm=builtin.PERM_NONE, field='owner_uid', priv=builtin.PRIV_NONE):
    return (doc[field] == self.user['_id']) and self.has_perm(perm) and self.has_priv(priv)

  async def update_session(self, *, new_saved=False, **kwargs):
    """Update or create session if necessary.

    If 'sid' in cookie, the 'expire_at' field is updated.
    If 'sid' not in cookie, only create when there is extra data.

    Args:
      new_saved: use saved session on creation.
      kwargs: extra data.

    Returns:
      The session document.
    """
    (sid, save), session = map(self.request.cookies.get, ['sid', 'save']), None
    if not sid:
      save = new_saved
    if save:
      token_type = token.TYPE_SAVED_SESSION
      session_expire_seconds = options.saved_session_expire_seconds
    else:
      token_type = token.TYPE_UNSAVED_SESSION
      session_expire_seconds = options.unsaved_session_expire_seconds
    if sid:
      session = await token.update(sid, token_type, session_expire_seconds,
                                   **{**kwargs,
                                      'update_ip': self.remote_ip,
                                      'update_ua': self.request.headers.get('User-Agent')})
    if kwargs and not session:
      sid, session = await token.add(token_type, session_expire_seconds,
                                     **{**kwargs,
                                        'create_ip': self.remote_ip,
                                        'create_ua': self.request.headers.get('User-Agent')})
    if session:
      cookie_kwargs = {'domain': options.cookie_domain,
                       'secure': options.cookie_secure,
                       'httponly': True}
      if save:
        timestamp = calendar.timegm(session['expire_at'].utctimetuple())
        cookie_kwargs['expires'] = utils.formatdate(timestamp, usegmt=True)
        cookie_kwargs['max_age'] = session_expire_seconds
        self.response.set_cookie('save', '1', **cookie_kwargs)
      self.response.set_cookie('sid', sid, **cookie_kwargs)
    else:
      self.clear_cookies('sid', 'save')
    return session or {}

  async def delete_session(self):
    sid, save = map(self.request.cookies.get, ['sid', 'save'])
    if sid:
      if save:
        token_type = token.TYPE_SAVED_SESSION
      else:
        token_type = token.TYPE_UNSAVED_SESSION
      await token.delete(sid, token_type)
    self.clear_cookies('sid', 'save')

  def clear_cookies(self, *names):
    for name in names:
      if name in self.request.cookies:
        self.response.set_cookie(name, '',
                                 expires=utils.formatdate(0, usegmt=True),
                                 domain=options.cookie_domain,
                                 secure=options.cookie_secure,
                                 httponly=True)

  @property
  def remote_ip(self):
    if options.ip_header:
      return self.request.headers.get(options.ip_header)
    else:
      return self.request.transport.get_extra_info('peername')[0]

  @property
  def csrf_token(self):
    if self.session:
      return _get_csrf_token(self.session['_id'])
    else:
      return ''

  def render_html(self, template_name, **kwargs):
    kwargs['handler'] = self
    if '_' not in kwargs:
      kwargs['_'] = self.translate
    kwargs['domain_id'] = self.domain_id
    if 'page_name' not in kwargs:
      kwargs['page_name'] = self.NAME
    if 'page_title' not in kwargs:
      kwargs['page_title'] = self.translate(self.TITLE)
    if 'path_components' not in kwargs:
      kwargs['path_components'] = self.build_path((self.translate(self.NAME), None))
    kwargs['reverse_url'] = self.reverse_url
    kwargs['datetime_span'] = self.datetime_span
    return template.Environment().get_template(template_name).render(kwargs)

  def render_title(self, page_title=None):
    if not page_title:
      page_title = self.translate(self.TITLE)
    if self.domain_id != builtin.DOMAIN_ID_SYSTEM:
      page_title += ' - {}'.format(self.domain['name'])
    page_title += ' - Vijos'
    return page_title

  async def send_mail(self, mail, title, template_name, **kwargs):
    content = self.render_html(template_name, url_prefix=options.url_prefix,
                               **kwargs)
    translate = self.translate
    if '_' in kwargs:
      translate = kwargs['_']
    await mailer.send_mail(mail, '{0} - Vijos'.format(translate(title)), content)


class Handler(web.View, HandlerBase):
  @asyncio.coroutine
  def __iter__(self):
    try:
      self.response = web.Response()
      yield from HandlerBase.prepare(self)
      yield from super(Handler, self).__iter__()
    except error.UserFacingError as e:
      _logger.warning("User facing error: %s", repr(e))
      self.response.set_status(e.http_status, None)
      if self.prefer_json:
        self.response.content_type = 'application/json'
        message = self.translate(e.message).format(*e.args)
        self.response.text = json.encode({'error': {**e.to_dict(), 'message': message}})
      else:
        self.render(e.template_name, error=e,
                    page_name='error', page_title=self.translate('error'),
                    path_components=self.build_path((self.translate('error'), None)))
    except Exception as e:
      _logger.error("Unexpected exception occurred when handling %s (IP = %s, UID = %d): %s",
                    self.url, self.remote_ip, (self.user and self.user['_id']) or None, repr(e))
      raise
    return self.response

  def render(self, template_name, **kwargs):
    self.response.content_type = 'text/html'
    self.response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate')
    self.response.headers.add('Pragma', 'no-cache')
    self.response.text = self.render_html(template_name, **kwargs)

  def json(self, obj):
    self.response.content_type = 'application/json'
    self.response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate')
    self.response.headers.add('Pragma', 'no-cache')
    self.response.text = json.encode(obj)

  async def binary(self, data, type='application/octet-stream'):
    self.response = web.StreamResponse()
    self.response.content_length = len(data)
    self.response.content_type = type
    await self.response.prepare(self.request)
    self.response.write(data)

  @property
  def prefer_json(self):
    for d in accept.parse(self.request.headers.get('Accept')):
      if d.media_type == 'application/json':
        return True
      elif d.media_type == 'text/html' or d.all_types:
        return False
    return False

  @property
  def url(self):
    return self.request.path

  @property
  def referer_or_main(self):
    return self.request.headers.get('referer') or self.reverse_url('domain_main')

  def redirect(self, redirect_url):
    self.response.set_status(web.HTTPFound.status_code, None)
    self.response.headers['Location'] = redirect_url

  def json_or_redirect(self, redirect_url, **kwargs):
    if self.prefer_json:
      self.json(kwargs)
    else:
      self.redirect(redirect_url)

  def json_or_render(self, template_name, **kwargs):
    if self.prefer_json:
      self.json(kwargs)
    else:
      self.render(template_name, **kwargs)

  @property
  def ui_context(self):
    return {'csrf_token': self.csrf_token,
            'cdn_prefix': options.cdn_prefix,
            'url_prefix': options.url_prefix}

  @property
  def user_context(self):
    return {'uid': self.user['_id'],
            'domain': self.domain_id}


class OperationHandler(Handler):
  DEFAULT_OPERATION = 'default'

  async def post(self):
    arguments = (await self.request.post()).copy()
    operation = arguments.pop('operation', self.DEFAULT_OPERATION)
    try:
      method = getattr(self, 'post_' + operation)
    except AttributeError:
      raise error.InvalidOperationError(operation) from None
    await method(**arguments)


class Connection(sockjs.Session, HandlerBase):
  def __init__(self, request, *args, **kwargs):
    super(Connection, self).__init__(*args, **kwargs)
    self.request = request
    self.response = web.Response()  # dummy response

  async def on_open(self):
    pass

  async def on_message(self, **kwargs):
    pass

  async def on_close(self):
    pass

  def send(self, **kwargs):
    super(Connection, self).send(json.encode(kwargs))


@functools.lru_cache()
def _get_csrf_token(session_id_binary):
  return hmac.new(b'csrf_token', session_id_binary, 'sha256').hexdigest()


@functools.lru_cache()
def _reverse_url(name, *, domain_id, **kwargs):
  if domain_id != builtin.DOMAIN_ID_SYSTEM:
    name += '_with_domain_id'
    kwargs['domain_id'] = domain_id
  if kwargs:
    return app.Application().router[name].url(parts=kwargs)
  else:
    return app.Application().router[name].url()


@functools.lru_cache()
def _build_path(*args, domain_id, domain_name):
  return [(domain_name, _reverse_url('domain_main', domain_id=domain_id)), *args]


@functools.lru_cache()
def _datetime_span(dt, relative=True, format='%Y-%m-%d %H:%M:%S', timezone=pytz.utc):
  if not dt.tzinfo:
    dt = dt.replace(tzinfo=pytz.utc)
  return markupsafe.Markup(
      '<span class="time{0}" data-timestamp="{1}">{2}</span>'.format(
          ' relative' if relative else '',
          calendar.timegm(dt.utctimetuple()),
          dt.astimezone(timezone).strftime(format)))


@functools.lru_cache()
def _datetime_stamp(dt):
  if not dt.tzinfo:
    dt = dt.replace(tzinfo=pytz.utc)
  return calendar.timegm(dt.utctimetuple())


# Decorators
def require_perm(perm):
  def decorate(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
      self.check_perm(perm)
      return func(self, *args, **kwargs)

    return wrapper

  return decorate


def require_priv(priv):
  def decorate(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
      self.check_priv(priv)
      return func(self, *args, **kwargs)

    return wrapper

  return decorate


def require_csrf_token(func):
  @functools.wraps(func)
  def wrapper(self, *args, **kwargs):
    if self.csrf_token and self.csrf_token != kwargs.pop('csrf_token', ''):
      raise error.CsrfTokenError()
    return func(self, *args, **kwargs)

  return wrapper


def route_argument(func):
  @functools.wraps(func)
  def wrapped(self, **kwargs):
    return func(self, **kwargs, **self.request.match_info)

  return wrapped


def get_argument(func):
  @functools.wraps(func)
  def wrapped(self, **kwargs):
    return func(self, **kwargs, **self.request.query)

  return wrapped


def post_argument(coro):
  @functools.wraps(coro)
  async def wrapped(self, **kwargs):
    return await coro(self, **kwargs, **await self.request.post())

  return wrapped


def limit_rate(op):
  def decorate(coro):
    @functools.wraps(coro)
    async def wrapped(self, **kwargs):
      await opcount.inc(**opcount.OPS[op], ident=opcount.PREFIX_IP + self.remote_ip)
      return await coro(self, **kwargs)

    return wrapped
  return decorate


def sanitize(func):
  @functools.wraps(func)
  def wrapped(self, **kwargs):
    for key, value in kwargs.items():
      try:
        kwargs[key] = func.__annotations__[key](value)
      except KeyError:
        raise error.UnknownArgumentError(key)
    return func(self, **kwargs)

  return wrapped
