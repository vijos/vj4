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


def is_id(s):
  return bool(re.fullmatch(r'[^\\/\s\u3000]([^\\/\n\r]*[^\\/\s\u3000])?', s))


def check_category_name(s):
  if not is_id(s):
    raise error.ValidationError('category_name')


def check_node_name(s):
  if not is_id(s):
    raise error.ValidationError('node_name')


def is_role(s):
  return bool(re.fullmatch(r'[_0-9A-Za-z]+', s))


def check_role(s):
  if not is_role(s):
    raise error.ValidationError('role')


def is_title(s):
  return bool(re.fullmatch(r'.{1,}', s))


def check_title(s):
  if not is_title(s):
    raise error.ValidationError('title')

def is_name(s):
  return bool(re.fullmatch(r'.{1,}', s))


def check_name(s):
  if not is_name(s):
    raise error.ValidationError('name')


def is_content(s):
  return isinstance(s, str) and len(str(s)) >= 2


def check_content(s):
  if not is_content(s):
    raise error.ValidationError('content')


def is_description(s):
  return isinstance(s, str)


def check_description(s):
  if not is_description(s):
    raise error.ValidationError('description')


def is_lang(i):
  return i in constant.language.LANG_TEXTS


def check_lang(i):
  if not is_lang(i):
    raise error.ValidationError('lang')
