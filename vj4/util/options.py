"""A command line parsing module which mimics tornado's interface."""
import argparse
import sys
import os

class Options(object):
  _parser = argparse.ArgumentParser()
  _namespace = argparse.Namespace()
  _dirty = False

  def define(self, name, default=None, help=None):
    flag_name = '--' + name.replace('_', '-')
    flag_type = type(default)
    if flag_type is bool:
      self._parser.add_argument(flag_name, dest=name, action='store_true', help=help)
      self._parser.add_argument('--no-' + name.replace('_', '-'), dest=name, action='store_false')
      self._parser.set_defaults(**{name: default})
    else:
      self._parser.add_argument(flag_name, dest=name, default=default, type=flag_type, help=help)
    self._dirty = True

  def __getattr__(self, item):
    if self._dirty:
      args_to_parse = []
      for k, v in os.environ.items(): # using environments start with `VJ_` as arguments
        if k.startswith('VJ_'):
          if k == 'VJ_CMDLINE_FLAGS': # for setting bool flags like `--debug` or `--no-pretty`
            args_to_parse.extend(v.split())
          else:
            args_to_parse.append('--' + k[3:].lower().replace('_','-'))
            args_to_parse.append(v)
      args_to_parse.extend(sys.argv[1:]) # cmdline args can override one in env

      self._parser.parse_known_args(args=args_to_parse, namespace=self._namespace)
      self._dirty = False
    return getattr(self._namespace, item)

  @property
  def leftovers(self):
    _, _leftovers = self._parser.parse_known_args(args=sys.argv[1:], namespace=self._namespace)
    return _leftovers

sys.modules[__name__] = Options()
