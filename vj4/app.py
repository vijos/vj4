import asyncio
import functools
import logging
import sockjs
from aiohttp import web
from os import path
from vj4 import error
from vj4.controller import smallcache
from vj4.model import bus
from vj4.util import json
from vj4.util import locale
from vj4.util import options
from vj4.util import tools

options.define('static', default=True, help='Serve static files.')
options.define('ip_header', default='X-Real-IP', help='Header name for remote IP.')
options.define('unsaved_session_expire_seconds', default=43200,
               help='Expire time for unsaved session, in seconds.')
options.define('saved_session_expire_seconds', default=2592000,
               help='Expire time for saved session, in seconds.')
options.define('cookie_domain', default=None, help='Cookie domain.')
options.define('cookie_secure', default=False, help='Enable secure cookie flag.')
options.define('registration_token_expire_seconds', default=86400,
               help='Expire time for registration token, in seconds.')
options.define('url_prefix', default='https://vijos.org', help='URL prefix.')
options.define('cdn_prefix', default='/', help='CDN prefix.')

_logger = logging.getLogger(__name__)

class Application(web.Application):
  def __init__(self):
    super(Application, self).__init__(
        handler_factory=functools.partial(web.RequestHandlerFactory, access_log=None),
        debug=options.options.debug)
    globals()[self.__class__.__name__] = lambda: self  # singleton

    # Initialize components.
    translation_path = path.join(path.dirname(__file__), 'locale')
    locale.load_translations(translation_path)
    self.loop.run_until_complete(asyncio.gather(tools.ensure_all_indexes(), bus.init()))
    smallcache.init()

    # Load views.
    from vj4.view import contest
    from vj4.view import discussion
    from vj4.view import home
    from vj4.view import judge
    from vj4.view import main
    from vj4.view import problem
    from vj4.view import record
    from vj4.view import training
    from vj4.view import user
    from vj4.view import i18n
    if options.options.static:
      self.router.add_static('/', path.join(path.dirname(__file__), '.uibuild'), name='static')

def route(url, name):
  def decorate(view):
    view.NAME = view.NAME or name
    view.TITLE = view.TITLE or name
    Application().router.add_route('*', url, view, name=name)
    Application().router.add_route('*', '/d/{domain_id}' + url, view, name=name + '_with_domain_id')
    return view
  return decorate

def connection_route(prefix, name):
  def decorate(conn):
    async def handler(msg, session):
      try:
        if msg.tp == sockjs.MSG_OPEN:
          await session.prepare()
          await session.on_open()
        elif msg.tp == sockjs.MSG_MESSAGE:
          await session.on_message(**json.decode(msg.data))
        elif msg.tp == sockjs.MSG_CLOSE:
          await session.on_close()
      except error.UserFacingError as e:
        _logger.warning("Websocket user facing error: %s", repr(e))
        session.close(4000, {'error': e.to_dict()})

    class Manager(sockjs.SessionManager):
      def get(self, id, create=False, request=None):
        if id not in self and create:
          self[id] = self._add(conn(request, id, self.handler,
                                    timeout=self.timeout, loop=self.loop, debug=self.debug))
        return self[id]

    sockjs.add_endpoint(Application(), handler, name=name, prefix=prefix,
                        manager=Manager(name, Application(), handler, Application().loop))
    return conn
  return decorate
