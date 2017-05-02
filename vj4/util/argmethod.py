"""Experimental helper module to wrap methods for command line invoke.

Usage example:

    python3.5 -m vj4.model.user --help
    python3.5 -m vj4.model.user -- --help
    python3.5 -m vj4.model.user get -1
    python3.5 -m vj4.model.user --db-name=prod get -1
"""
import collections
import logging
import logging.config

from vj4 import db
from vj4.util import options

options.define('pretty', default=False, help='Pretty print the result.')

_methods = collections.OrderedDict()


def wrap(method):
  if method.__module__ == '__main__':
    _methods[method.__name__] = method
  return method


def invoke_by_args():
  logging.config.dictConfig({
    'version': 1,
    'handlers': {
      'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'colored',
      },
    },
    'formatters': {
      'colored': {
        '()': 'colorlog.ColoredFormatter',
        'format': '%(log_color)s[%(levelname).1s '
                  '%(asctime)s %(module)s:%(lineno)d]%(reset)s %(message)s',
        'datefmt': '%y%m%d %H:%M:%S'
      }
    },
    'root': {
      'level': 'INFO',
      'handlers': ['console'],
    },
    'disable_existing_loggers': False,
  })
  import argparse
  import asyncio
  import inspect
  import pprint
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest='')
  for name, method in _methods.items():
    subparser = subparsers.add_parser(name)
    argcount = method.__code__.co_argcount
    num_defaults = len(method.__defaults__) if method.__defaults__ else 0
    argoffset = argcount - num_defaults
    for index, argname in enumerate(method.__code__.co_varnames[:argcount]):
      if index < argoffset:
        subparser.add_argument(argname, type=method.__annotations__[argname])
      elif argname in method.__annotations__:
        subparser.add_argument(argname,
                               type=method.__annotations__[argname],
                               nargs='?',
                               default=method.__defaults__[index - argoffset])
  args = parser.parse_args(options.leftovers)
  name = getattr(args, '')
  delattr(args, '')
  if not name:
    parser.print_help()
  else:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db.init_db2())
    try:
      result = _methods[name](**vars(args))
      if inspect.iscoroutine(result):
        result = loop.run_until_complete(result)
      if options.pretty:
        print_func = pprint.pprint
      else:
        print_func = lambda x: print(x) if x is not None else None
      if hasattr(result, '__aiter__'):
        async def aloop():
          async for entry in result:
            print_func(entry)

        loop.run_until_complete(aloop())
      else:
        print_func(result)
    except KeyboardInterrupt:
      pass
    loop.set_exception_handler(lambda loop, context: None)
