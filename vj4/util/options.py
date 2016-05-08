"""A command line parsing module which mimics tornado's interface."""
import argparse
import logging.config

LOG_FORMAT = '%(log_color)s[%(levelname).1s %(asctime)s %(module)s:%(lineno)d]%(reset)s %(message)s'

_parsed = False
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
  if _parsed:
    _parser.parse_known_args(namespace=options)

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
  global _parsed
  _parsed = True
  _, argv = _parser.parse_known_args(namespace=options)
  enable_pretty_logging()
  return argv

define('debug', default=False, help='Enable debug mode.')
