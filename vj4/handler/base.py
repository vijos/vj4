import asyncio
import calendar
import functools
import hmac
import logging
from email import utils

import accept
import markupsafe
import pytz
import sockjs
from aiohttp import web

from vj4 import app
from vj4 import error
from vj4 import template
from vj4.model import builtin
from vj4.model import domain
from vj4.model import token
from vj4.model import user
from vj4.model.adaptor import setting
from vj4.util import json
from vj4.util import locale
from vj4.util import options

_logger = logging.getLogger(__name__)


class HandlerBase(setting.SettingMixin):
  NAME = None
  TITLE = None

  async def prepare(self):
    self.session = await self.update_session()
    if self.session and 'uid' in self.session:
      self.user = await user.get_by_uid(self.session['uid']) or builtin.USER_GUEST
    else:
      self.user = builtin.USER_GUEST
    self.translate = locale.get_translate(self.get_setting('view_lang'))
    # TODO(iceboy): use user timezone.
    self.datetime_span = _get_datetime_span('Asia/Shanghai')
    self.domain_id = self.request.match_info.pop('domain_id', builtin.DOMAIN_ID_SYSTEM)
    self.reverse_url = functools.partial(_reverse_url, domain_id=self.domain_id)
    self.build_path = functools.partial(_build_path, domain_id=self.domain_id)
    self.domain = await domain.get(self.domain_id)
    if not self.domain:
      raise error.DomainNotFoundError(self.domain_id)

  def has_perm(self, perm):
    role = self.user['roles'].get(self.domain_id, builtin.ROLE_DEFAULT)
    mask = self.domain['roles'].get(role, builtin.PERM_NONE)
    return (perm & mask) == perm or self.domain['owner_uid'] == self.user['_id']

  def check_perm(self, perm):
    if not self.has_perm(perm):
      raise error.PermissionError(perm)

  def has_priv(self, priv):
    return (priv & self.user['priv']) == priv

  def check_priv(self, priv):
    if not self.has_priv(priv):
      raise error.PrivilegeError(priv)

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
      session_expire_seconds = options.options.saved_session_expire_seconds
    else:
      token_type = token.TYPE_UNSAVED_SESSION
      session_expire_seconds = options.options.unsaved_session_expire_seconds
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
      cookie_kwargs = {'domain': options.options.cookie_domain,
                       'secure': options.options.cookie_secure,
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
                                 domain=options.options.cookie_domain,
                                 secure=options.options.cookie_secure,
                                 httponly=True)

  @property
  def remote_ip(self):
    if options.options.ip_header:
      return self.request.headers.get(options.options.ip_header)
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
    kwargs['_'] = self.translate
    kwargs['domain_id'] = self.domain_id
    if not 'page_name' in kwargs:
      kwargs['page_name'] = self.NAME
    if 'page_title' not in kwargs:
      kwargs['page_title'] = self.translate(self.TITLE)
    if 'path_components' not in kwargs:
      kwargs['path_components'] = self.build_path((self.translate(self.NAME), None))
    kwargs['reverse_url'] = self.reverse_url
    kwargs['datetime_span'] = self.datetime_span
    return template.Environment().get_template(template_name).render(kwargs)


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
        self.response.text = json.encode({'error': e.to_dict()})
      else:
        self.render(e.template_name, error=e,
                    page_name='error', page_title=self.translate('error'),
                    path_components=self.build_path((self.translate('error'), None)))
    return self.response

  def render(self, template_name, **kwargs):
    self.response.content_type = 'text/html'
    self.response.text = self.render_html(template_name, **kwargs)

  def json(self, obj):
    self.response.content_type = 'application/json'
    self.response.text = json.encode(obj)

  async def binary(self, data):
    self.response = web.StreamResponse()
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
  def referer_or_main(self):
    return self.request.headers.get('referer', self.reverse_url('main'))

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
            'cdn_prefix': options.options.cdn_prefix,
            'url_prefix': options.options.url_prefix}


class OperationView(Handler):
  async def post(self):
    arguments = (await self.request.post()).copy()
    operation = arguments.pop('operation')
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
def _build_path(*args, domain_id):
  return [(domain_id, _reverse_url('main', domain_id=domain_id)), *args]


@functools.lru_cache()
def _get_datetime_span(tzname):
  tz = pytz.timezone(tzname)

  @functools.lru_cache()
  def _datetime_span(dt):
    if not dt.tzinfo:
      dt = dt.replace(tzinfo=pytz.utc)
    # TODO(iceboy): add a class for javascript selection.
    return markupsafe.Markup(
      '<span data-timestamp="{0}">{1}</span>'.format(
        int(dt.astimezone(pytz.utc).timestamp()),
        dt.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')))

  return _datetime_span


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
    return func(self, **kwargs, **self.request.GET)

  return wrapped


def post_argument(coro):
  @functools.wraps(coro)
  async def wrapped(self, **kwargs):
    return await coro(self, **kwargs, **await self.request.post())

  return wrapped


def sanitize(func):
  @functools.wraps(func)
  def wrapped(self, **kwargs):
    for key, value in kwargs.items():
      kwargs[key] = func.__annotations__[key](value)
    return func(self, **kwargs)

  return wrapped
