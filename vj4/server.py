import atexit
import coloredlogs
import logging
import os
import signal
import socket
import sys
import urllib.parse

from aiohttp import web
from vj4 import app
from vj4.util import options

options.define('listen', default='http://127.0.0.1:8888', help='Server listening address.')
options.define('prefork', default=1, help='Number of prefork workers.')

_logger = logging.getLogger(__name__)


def main():
  coloredlogs.install(level=logging.DEBUG if options.debug else logging.INFO,
                      fmt='[%(levelname).1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                      datefmt='%y%m%d %H:%M:%S')
  logging.getLogger('sockjs').setLevel(logging.WARNING)
  url = urllib.parse.urlparse(options.listen)
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
  for i in range(1, options.prefork):
    pid = os.fork()
    if not pid:
      break
    else:
      atexit.register(lambda: os.kill(pid, signal.SIGTERM))
  web.run_app(app.Application(), sock=sock, access_log=None, shutdown_timeout=0)

if __name__ == '__main__':
  sys.exit(main())
