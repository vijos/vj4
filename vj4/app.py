import logging
from os import path

import sanic
import sanic.response

from vj4 import error
from vj4.service import bus
from vj4.service import smallcache
from vj4.service import staticmanifest
from vj4.util import json
from vj4.util import locale
from vj4.util import options
from vj4.util import tools

options.define('debug', default=False, help='Enable debug mode.')
options.define('static', default=True, help='Serve static files.')
options.define('ip_header', default='X-Forwarded-For', help='Header name for remote IP.')
options.define('unsaved_session_expire_seconds', default=43200,
               help='Expire time for unsaved session, in seconds.')
options.define('saved_session_expire_seconds', default=2592000,
               help='Expire time for saved session, in seconds.')
options.define('cookie_domain', default=None, help='Cookie domain.')
options.define('cookie_secure', default=False, help='Enable secure cookie flag.')
options.define('registration_token_expire_seconds', default=86400,
               help='Expire time for registration token, in seconds.')
options.define('lostpass_token_expire_seconds', default=3600,
               help='Expire time for lostpass token, in seconds.')
options.define('changemail_token_expire_seconds', default=3600,
               help='Expire time for changemail token, in seconds.')
options.define('url_prefix', default='https://vijos.org', help='URL prefix.')
options.define('cdn_prefix', default='/', help='CDN prefix.')

_logger = logging.getLogger(__name__)


class Application(sanic.Sanic):
  def __init__(self):
    super(Application, self).__init__()
    globals()[self.__class__.__name__] = lambda: self  # singleton

    static_path = path.join(path.dirname(__file__), '.uibuild')
    translation_path = path.join(path.dirname(__file__), 'locale')

    # Initialize components.
    staticmanifest.init(static_path)
    locale.load_translations(translation_path)
    self.add_task(tools.ensure_all_indexes())
    self.add_task(bus.init())
    smallcache.init()

    # Load views.
    # TODO(iceboy): Restore commented modules after supporting sockjs and multipart.
    from vj4.handler import contest
    from vj4.handler import discussion
    from vj4.handler import domain
    #from vj4.handler import fs
    #from vj4.handler import home
    #from vj4.handler import judge
    from vj4.handler import misc
    #from vj4.handler import problem
    #from vj4.handler import record
    from vj4.handler import training
    from vj4.handler import user
    from vj4.handler import i18n
    if options.static:
      self.static('/', static_path)


def route(url, name):
  def decorate(handler_type):
    handler_type.NAME = handler_type.NAME or name
    handler_type.TITLE = handler_type.TITLE or name

    class Handler(object):
      view_class = handler_type

      def __init__(self, name):
        self.__name__ = name

      async def __call__(self, request, **kwargs):
        handler = handler_type()
        handler.request = request
        handler.response = sanic.response.HTTPResponse()
        handler.route_args = kwargs
        await handler.handle()
        return handler.response

    Application().add_route(Handler(name), url)
    Application().add_route(Handler(name + '_with_domain_id'), '/d/<domain_id>' + url)
    return handler_type

  return decorate

"""
def connection_route(prefix, name):
  def decorate(conn):
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
      def get(self, id, create=False, request=None):
        if id not in self and create:
          self[id] = self._add(conn(request, id, self.handler,
                                    timeout=self.timeout, loop=self.loop, debug=self.debug))
        return self[id]

    sockjs.add_endpoint(Application(), handler, name=name, prefix=prefix,
                        manager=Manager(name, Application(), handler, Application().loop))
    sockjs.add_endpoint(Application(), handler,
                        name=name + '_with_domain_id', prefix='/d/{domain_id}' + prefix,
                        manager=Manager(name + '_with_domain_id', Application(), handler,
                                        Application().loop))
    return conn

  return decorate
"""