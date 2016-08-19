import re

from vj4 import constant
from vj4 import error
from vj4.model import builtin


def is_uid(s):
  return bool(re.fullmatch(r'-?\d+', s))


def check_uid(s):
  if not is_uid(s):
    raise error.ValidationError('uid')


def is_uname(s):
  return bool(re.fullmatch(r'[^\s\u3000](.*[^\s\u3000])?', s))


def check_uname(s):
  if not is_uname(s):
    raise error.ValidationError('uname')


def is_password(s):
  return bool(re.fullmatch(r'.{5,}', s))


def check_password(s):
  if not is_password(s):
    raise error.ValidationError('password')


def is_mail(s):
  return bool(re.fullmatch(r'\w+([-+.]\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*', s))


def check_mail(s):
  if not is_mail(s):
    raise error.ValidationError('mail')


def is_domain_id(s):
  return bool(re.fullmatch(r'[^0-9\\/\s\u3000][^\\/\n\r]{2,}[^\\/\s\u3000]', s))


def check_domain_id(s):
  if not is_domain_id(s):
    raise error.ValidationError('domain_id')


def is_title(s):
  return bool(re.fullmatch(r'.{1,}', s))


def check_title(s):
  if not is_title(s):
    raise error.ValidationError('title')


def is_content(s):
  return len(str(s)) >= 2


def check_content(s):
  if not is_content(s):
    raise error.ValidationError('content')


def is_description(s):
  return len(str(s)) >= 0


def check_description(s):
  if not is_description(s):
    raise error.ValidationError('description')


def is_lang(i):
  return i in constant.language.LANG_TEXTS


def check_lang(i):
  if not is_lang(i):
    raise error.ValidationError('lang')
