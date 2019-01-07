"""A locale module which mimics tornado's interface."""
import collections
import os
import os.path
import yaml

from vj4.util import options

options.define('default_locale', default='zh_CN', help='Default locale.')

_locales = {}


def _init():
  translation_path = os.path.join(os.path.dirname(__file__), '..', 'locale')
  langs = []
  for filename in os.listdir(translation_path):
    if not filename.endswith(".yaml"):
      continue
    with open(os.path.join(translation_path, filename), encoding='utf-8') as yaml_file:
      code = filename[:-5]
      name = yaml_file.readline()[1:].strip()
      locale = yaml.load(yaml_file)
      _locales[code] = locale
      if code == options.default_locale:
        global _default_locale
        _default_locale = locale
      langs.append((code, name))
  global VIEW_LANGS
  VIEW_LANGS = collections.OrderedDict(langs)


def get(locale_code):
  return _locales.get(locale_code, _default_locale)

_init()
