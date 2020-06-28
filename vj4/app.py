import asyncio
import datetime
import logging
from os import path

import aiohttp_sentry
import sockjs
from aiohttp import web

from vj4 import db
from vj4 import error
from vj4.model import system
from vj4.service import bus
from vj4.service import smallcache
from vj4.service import staticmanifest
from vj4.util import json
from vj4.util import options
from vj4.util import tools

options.define('debug', default=False, help='Enable debug mode.')
options.define('static', default=True, help='Serve static files.')
options.define('ip_header', default='', help='Header name for remote IP.')
options.define('unsaved_session_expire_seconds', default=43200,
               help='Expire time for unsaved session, in seconds.')
options.define('saved_session_expire_seconds', default=2592000,
               help='Expire time for saved session, in seconds.')
options.define('cookie_domain', default='', help='Cookie domain.')
options.define('cookie_secure', default=False, help='Enable secure cookie flag.')
options.define('registration_token_expire_seconds', default=86400,
               help='Expire time for registration token, in seconds.')
options.define('lostpass_token_expire_seconds', default=3600,
               help='Expire time for lostpass token, in seconds.')
options.define('changemail_token_expire_seconds', default=3600,
               help='Expire time for changemail token, in seconds.')
options.define('url_prefix', default='https://vijos.org', help='URL prefix.')
options.define('cdn_prefix', default='/', help='CDN prefix.')
options.define('sentry_dsn', default='', help='Sentry integration DSN.')

_logger = logging.getLogger(__name__)


class SentryMiddleware(aiohttp_sentry.SentryMiddleware): # For getting a correct client IP
  async def get_extra_data(self, request):
    return {
      'request': {
        'query_string': request.query_string,
        'headers': dict(request.headers),
        'url': request.path,
        'method': request.method,
        'scheme': request.scheme,
        'env': {
          'REMOTE_ADDR': tools.get_remote_ip(request),
        }
      }
    }


class Application(web.Application):
  def __init__(self):
    middlewares = []
    if options.sentry_dsn:
      middlewares.append(SentryMiddleware({
        'dsn': options.sentry_dsn,
        'environment': 'vj4',
        'debug': options.debug,
      }))

    super(Application, self).__init__(
      debug=options.debug,
      middlewares=middlewares
    )
    globals()[self.__class__.__name__] = lambda: self  # singleton

    static_path = path.join(path.dirname(__file__), '.uibuild')

    # Initialize components.
    staticmanifest.init(static_path)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db.init())
    loop.run_until_complete(system.setup())
    loop.run_until_complete(system.ensure_db_version())
    loop.run_until_complete(asyncio.gather(tools.ensure_all_indexes(), bus.init()))
    smallcache.init()

    # Load views.
    from vj4.handler import contest
    from vj4.handler import discussion
    from vj4.handler import domain
    from vj4.handler import fs
    from vj4.handler import home
    from vj4.handler import homework
    from vj4.handler import judge
    from vj4.handler import misc
    from vj4.handler import problem
    from vj4.handler import record
    from vj4.handler import training
    from vj4.handler import ranking
    from vj4.handler import user
    from vj4.handler import i18n
    if options.static:
      self.router.add_static('/', static_path, name='static')


def route(url, name, global_route=False):
  def decorate(handler):
    handler.NAME = handler.NAME or name
    handler.TITLE = handler.TITLE or name
    handler.GLOBAL = global_route
    Application().router.add_route('*', url, handler, name=name)
    Application().router.add_route('*', '/d/{domain_id}' + url, handler,
                                   name=name + '_with_domain_id')
    return handler

  return decorate


def connection_route(prefix, name, global_route=False):
  def decorate(conn):
    conn.GLOBAL = global_route
    async def handler(msg, session):
      try:
        if msg.tp == sockjs.MSG_OPEN:
          await session.prepare()
          await session.on_open()
        elif msg.tp == sockjs.MSG_MESSAGE:
          await session.on_message(**json.decode(msg.data))
        elif msg.tp == sockjs.MSG_CLOSED:
          await session.on_close()
      except error.UserFacingError as e:
        _logger.warning("Websocket user facing error: %s", repr(e))
        session.close(4000, {'error': e.to_dict()})

    class Manager(sockjs.SessionManager):
      def __init__(self, *args):
        super(Manager, self).__init__(*args)
        self.factory = conn
        self.timeout = datetime.timedelta(seconds=60)

    loop = asyncio.get_event_loop()
    sockjs.add_endpoint(Application(), handler, name=name, prefix=prefix,
                        manager=Manager(name, Application(), handler, loop))
    sockjs.add_endpoint(
        Application(), handler, name=name + '_with_domain_id', prefix='/d/{domain_id}' + prefix,
        manager=Manager(name + '_with_domain_id', Application(), handler, loop))
    return conn

  return decorate
