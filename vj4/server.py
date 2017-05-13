import logging
import os
import socket
import sys
import urllib.parse

from vj4 import app
from vj4.util import options

options.define('listen', default='http://127.0.0.1:8888', help='Server listening address.')
options.define('prefork', default=1, help='Number of prefork workers.')

_logger = logging.getLogger(__name__)


def main():
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
  _logger.info('Server listening on %s', options.listen)
  app.Application().run(host=None, port=None, sock=sock, workers=options.prefork, log_config=None)

if __name__ == '__main__':
  sys.exit(main())
