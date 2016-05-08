import asyncio
import os
from vj4 import app
from vj4.util import options

options.define('path', default='/tmp/vijos.sock', help='UNIX socket path.')

if __name__ == '__main__':
  options.parse_command_line()
  try:
    os.remove(options.options.path)
  except OSError:
    pass
  loop = asyncio.get_event_loop()
  loop.run_until_complete(
      loop.create_unix_server(app.Application().make_handler(), options.options.path))
  loop.run_forever()
