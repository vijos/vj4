"""A command line parsing module which mimics tornado's interface."""
import argparse
import sys

_parser = argparse.ArgumentParser()
options = argparse.Namespace()
leftovers = sys.argv[1:]


def define(name, default=None, help=None):
  flag_name = '--' + name.replace('_', '-')
  flag_type = type(default)
  if flag_type is bool:
    _parser.add_argument(flag_name, dest=name, action='store_true', help=help)
    _parser.add_argument('--no-' + name.replace('_', '-'), dest=name, action='store_false')
    _parser.set_defaults(**{name: default})
  else:
    _parser.add_argument(flag_name, dest=name, default=default, type=flag_type, help=help)
  global leftovers
  _, leftovers = _parser.parse_known_args(args=sys.argv[1:], namespace=options)
