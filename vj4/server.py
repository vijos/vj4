import atexit
import coloredlogs
import logging
import os
import shutil
import signal
import socket
import sys
import urllib.parse

from aiohttp import web
from coloredlogs import syslog
from vj4 import app
from vj4.util import options

options.define('listen', default='http://127.0.0.1:8888', help='Server listening address.')
options.define('prefork', default=1, help='Number of prefork workers.')
options.define('syslog', default=False, help='Use syslog instead of stderr for logging.')
options.define('listen_owner', default='www-data', help='Owner of the socket when server is listening to a unix socket.')
options.define('listen_group', default='www-data', help='Group of the socket when server is listening to a unix socket.')
options.define('listen_mode', default='660', help='File mode of the socket when server is listening to a unix socket.')

_logger = logging.getLogger(__name__)


def main():
  if not options.syslog:
    coloredlogs.install(level=logging.DEBUG if options.debug else logging.INFO,
                        fmt='[%(levelname).1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                        datefmt='%y%m%d %H:%M:%S')
  else:
    syslog.enable_system_logging(level=logging.DEBUG if options.debug else logging.INFO,
                                 fmt='vj4[%(process)d] %(programname)s %(levelname).1s %(message)s')
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
    shutil.chown(url.path, options.listen_owner, options.listen_group)
    os.chmod(url.path, int(options.listen_mode, 8))
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
