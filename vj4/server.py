import asyncio
import socket
from aiohttp import web
from vj4 import app
from vj4.util import options
from vj4.util import prefork

options.define('host', default='', help='HTTP server host.')
options.define('port', default=8888, help='HTTP server port.')

if __name__ == '__main__':
  options.parse_command_line()
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
  sock.bind((options.options.host, options.options.port))
  prefork.prefork()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(loop.create_server(app.Application().make_handler(), sock=sock))
  loop.run_forever()
