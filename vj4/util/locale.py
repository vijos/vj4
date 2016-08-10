"""A locale module which mimics tornado's interface."""
import csv
import functools
import os
import os.path

from vj4.util import options

options.define('default_locale', default='zh_CN', help='Default locale.')

_locales = {}


def load_translations(translation_path):
  for path in os.listdir(translation_path):
    if not path.endswith(".csv"):
      continue
    with open(os.path.join(translation_path, path), encoding='utf-8') as csv_file:
      _locales[path[:-4]] = dict(csv.reader(csv_file))


@functools.lru_cache()
def get_translate(locale_code):
  if locale_code not in _locales:
    locale_code = options.options.default_locale
  locale = _locales[locale_code]
  return lambda text: locale[text] if text in locale else text
