import re

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


def is_gender(i):
  return i in builtin.USER_GENDERS


def check_gender(i):
  if not is_gender(i):
    raise error.ValidationError('gender')
