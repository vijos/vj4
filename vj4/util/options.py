"""A command line parsing module which mimics tornado's interface."""
import argparse
import logging.config
import sys

LOG_FORMAT = '%(log_color)s[%(levelname).1s %(asctime)s %(module)s:%(lineno)d]%(reset)s %(message)s'

_args = None
_parser = argparse.ArgumentParser()
options = argparse.Namespace()


def define(name, default=None, help=None):
  flag_name = '--' + name.replace('_', '-')
  flag_type = type(default)
  if flag_type is bool:
    _parser.add_argument(flag_name, dest=name, action='store_true', help=help)
    _parser.add_argument('--no-' + name.replace('_', '-'), dest=name, action='store_false')
    _parser.set_defaults(**{name: default})
  else:
    _parser.add_argument(flag_name, dest=name, default=default, type=flag_type, help=help)
  if _args is not None:
    _parser.parse_known_args(args=_args, namespace=options)


def enable_pretty_logging():
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
        'format': LOG_FORMAT,
        'datefmt': '%y%m%d %H:%M:%S'
      }
    },
    'root': {
      'level': 'DEBUG' if options.debug else 'INFO',
      'handlers': ['console'],
    },
    'disable_existing_loggers': False,
  })


def parse_command_line():
  global _args
  _args = sys.argv[1:]
  _, argv = _parser.parse_known_args(args=_args, namespace=options)
  enable_pretty_logging()
  return argv


def set_default_for_test():
  global _args
  _args = ''
  _parser.parse_known_args(args=_args, namespace=options)


define('debug', default=False, help='Enable debug mode.')
