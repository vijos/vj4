import re

from vj4 import constant
from vj4 import error


UID_RE = re.compile(r'-?\d+')
UNAME_RE = re.compile(r'[^\s\u3000](.{,254}[^\s\u3000])?')
MAIL_RE = re.compile(r'\w+([-+.\w]+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*')
# TODO(twd2): unicode char
DOMAIN_ID_RE = re.compile(r'[_A-Za-z][_0-9A-Za-z]{3,255}')
ID_RE = re.compile(r'[^\\/\s\u3000]([^\\/\n\r]*[^\\/\s\u3000])?')
ROLE_RE = re.compile(r'[_0-9A-Za-z]{1,256}')
DOMAIN_INVITATION_CODE_RE = re.compile(r'[0-9A-Za-z]{1,64}')


def is_uid(s):
  return bool(UID_RE.fullmatch(s))


def check_uid(s):
  if not is_uid(s):
    raise error.ValidationError('uid')


def is_uname(s):
  return bool(UNAME_RE.fullmatch(s))


def check_uname(s):
  if not is_uname(s):
    raise error.ValidationError('uname')


def is_password(s):
  return len(s) >= 5


def check_password(s):
  if not is_password(s):
    raise error.ValidationError('password')


def is_mail(s):
  return bool(MAIL_RE.fullmatch(s))


def check_mail(s):
  if not is_mail(s):
    raise error.ValidationError('mail')


def is_domain_id(s):
  return bool(DOMAIN_ID_RE.fullmatch(s))


def check_domain_id(s):
  if not is_domain_id(s):
    raise error.ValidationError('domain_id')


def is_id(s):
  return bool(ID_RE.fullmatch(s))


def check_category_name(s):
  if not is_id(s):
    raise error.ValidationError('category_name')


def check_node_name(s):
  if not is_id(s):
    raise error.ValidationError('node_name')


def is_role(s):
  return bool(ROLE_RE.fullmatch(s))


def check_role(s):
  if not is_role(s):
    raise error.ValidationError('role')


def is_title(s):
  return 0 < len(s.strip()) <= 64


def check_title(s):
  if not is_title(s):
    raise error.ValidationError('title')


def is_name(s):
  return 0 < len(s.strip()) <= 256


def check_name(s):
  if not is_name(s):
    raise error.ValidationError('name')


def is_content(s):
  return isinstance(s, str) and 0 < len(s.strip()) < 65536


def check_content(s):
  if not is_content(s):
    raise error.ValidationError('content')


def is_intro(s):
  return isinstance(s, str) and 0 < len(s.strip()) < 500


def check_intro(s):
  if not is_intro(s):
    raise error.ValidationError('intro')


def is_description(s):
  return isinstance(s, str) and len(s) < 65536


def check_description(s):
  if not is_description(s):
    raise error.ValidationError('description')


def is_bulletin(s):
  return isinstance(s, str) and len(s) < 65536


def check_bulletin(s):
  if not is_bulletin(s):
    raise error.ValidationError('bulletin')


def is_lang(i):
  return i in constant.language.LANG_TEXTS


def check_lang(i):
  if not is_lang(i):
    raise error.ValidationError('lang')


def is_domain_invitation_code(s):
  return bool(DOMAIN_INVITATION_CODE_RE.fullmatch(s))


def check_domain_invitation_code(s):
  if not is_domain_invitation_code(s):
    raise error.ValidationError('invitation_code')
