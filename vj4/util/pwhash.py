import base64
import binascii
import functools
import hashlib
import os

from vj4 import error
from vj4.util import argmethod

_HASH_TYPE_VJ2 = 'vj2'
_HASH_TYPE_VJ4 = 'vj4'


def _md5(s):
  return hashlib.md5(s.encode()).hexdigest()


def _sha1(s):
  return hashlib.sha1(s.encode()).hexdigest()


def _b64encode(s):
  return base64.b64encode(s.encode()).decode()


def _b64decode(s):
  return base64.b64decode(s.encode()).decode()


@argmethod.wrap
def gen_salt(byte_length: int=20):
  return binascii.hexlify(os.urandom(byte_length)).decode()


@argmethod.wrap
def hash_vj2(uname: str, password: str, salt: str):
  password_md5 = _md5(password)
  mixed_sha1 = _sha1(_md5(uname.lower() + password_md5) +
                     salt +
                     _sha1(password_md5 + salt))
  return _HASH_TYPE_VJ2 + '|' + _b64encode(uname) + '|' + mixed_sha1


@argmethod.wrap
def hash_vj4(password: str, salt: str):
  dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
  return _HASH_TYPE_VJ4 + '|' + binascii.hexlify(dk).decode()


@argmethod.wrap
@functools.lru_cache()
def check(password: str, salt: str, hash: str):
  hash_type, rest = hash.split('|', 1)
  if hash_type == _HASH_TYPE_VJ2:
    uname_b64 = rest.split('|', 1)[0]
    uname = _b64decode(uname_b64)
    return hash == hash_vj2(uname, password, salt)
  elif hash_type == _HASH_TYPE_VJ4:
    return hash == hash_vj4(password, salt)
  else:
    raise error.HashError('unsupported hash type')


@argmethod.wrap
def need_upgrade(hash: str):
  hash_type, rest = hash.split('|', 1)
  return hash_type != _HASH_TYPE_VJ4


if __name__ == '__main__':
  argmethod.invoke_by_args()
