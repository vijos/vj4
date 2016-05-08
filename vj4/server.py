import logging
from aiohttp import web
from vj4 import app
from vj4.util import options

options.define('port', default=8888, help='HTTP server port.')

_logger = logging.getLogger(__name__)

if __name__ == '__main__':
  options.parse_command_line()
  web.run_app(app.Application(),
              port=options.options.port,
              print=lambda s: [logging.info(l) for l in s.splitlines()])
