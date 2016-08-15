"""A locale module which mimics tornado's interface."""
import collections
import functools
import os
import os.path
import yaml

from vj4.util import options

options.define('default_locale', default='zh_CN', help='Default locale.')

_locales = {}

# View langs.
VIEW_LANGS = {}


def load_translations(translation_path):
  langs = []
  for filename in os.listdir(translation_path):
    if not filename.endswith(".yaml"):
      continue
    with open(os.path.join(translation_path, filename), encoding='utf-8') as yaml_file:
      code = filename[:-5]
      name = yaml_file.readline()[1:].strip()
      _locales[code] = yaml.load(yaml_file)
      langs.append((code, name))
  global VIEW_LANGS
  VIEW_LANGS = collections.OrderedDict(langs)


@functools.lru_cache()
def get_translate(locale_code):
  if locale_code not in _locales:
    locale_code = options.options.default_locale
  locale = _locales[locale_code]
  return lambda text: locale[text] if text in locale else text
