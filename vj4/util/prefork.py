import atexit
import os
import signal
from vj4.util import options

options.define('prefork', default=1, help='Number of prefork workers.')

def prefork():
  for i in range(1, options.options.prefork):
    pid = os.fork()
    if not pid:
      break
    else:
      atexit.register(lambda: os.kill(pid, signal.SIGTERM))
