import asyncio
import atexit
import os
import signal
import socket
from vj4 import app
from vj4.util import options

options.define('path', default='/tmp/vijos.sock', help='UNIX socket path.')
options.define('prefork', default=1, help='Number of prefork workers.')

if __name__ == '__main__':
  options.parse_command_line()
  sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
  try:
    os.remove(options.options.path)
  except FileNotFoundError:
    pass
  sock.bind(options.options.path)

  for i in range(1, options.options.prefork):
    pid = os.fork()
    if not pid:
      break
    else:
      atexit.register(lambda: os.kill(pid, signal.SIGTERM))

  loop = asyncio.get_event_loop()
  loop.run_until_complete(loop.create_unix_server(app.Application().make_handler(), sock=sock))
  loop.run_forever()
