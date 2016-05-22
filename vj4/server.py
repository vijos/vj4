import asyncio
import atexit
import logging
import os
import signal
import socket
import sys
import urllib.parse
from vj4 import app
from vj4.util import options

options.define('listen', default='http://127.0.0.1:8888', help='Server listening address.')
options.define('prefork', default=1, help='Number of prefork workers.')

_logger = logging.getLogger(__name__)

def main():
  options.parse_command_line()
  _logger.info('Server listening on %s', options.options.listen)
  url = urllib.parse.urlparse(options.options.listen)
  if url.scheme == 'http':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    host, port_str = url.netloc.rsplit(':', 1)
    sock.bind((host, int(port_str)))
  elif url.scheme == 'unix':
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
      os.remove(url.path)
    except FileNotFoundError:
      pass
    sock.bind(url.path)
  else:
    _logger.error('Invalid listening scheme %s', url.scheme)
    return 1
  for i in range(1, options.options.prefork):
    pid = os.fork()
    if not pid:
      break
    else:
      atexit.register(lambda: os.kill(pid, signal.SIGTERM))
  loop = asyncio.get_event_loop()
  loop.run_until_complete(loop.create_server(app.Application().make_handler(), sock=sock))
  loop.run_forever()

if __name__ == '__main__':
  sys.exit(main())
