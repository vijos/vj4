import asyncio
import os
import socket
from vj4 import app
from vj4.util import options
from vj4.util import prefork

options.define('path', default='/tmp/vijos.sock', help='UNIX socket path.')

if __name__ == '__main__':
  options.parse_command_line()
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  try:
    os.remove(options.options.path)
  except FileNotFoundError:
    pass
  sock.bind(options.options.path)
  prefork.prefork()
  loop = asyncio.get_event_loop()
  loop.run_until_complete(loop.create_unix_server(app.Application().make_handler(), sock=sock))
  loop.run_forever()
