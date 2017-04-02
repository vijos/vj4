from os import path
from vj4.util import json


MANIFEST_FILE = 'static-manifest.json'
_manifest_dir = None
_manifest_path = None
_manifest = {}


def init(static_dir):
  global _manifest_dir, _manifest_path, _manifest
  _manifest_dir = static_dir
  _manifest_path = path.join(_manifest_dir, MANIFEST_FILE)
  try:
    with open(_manifest_path, 'r') as manifest_file:
      data = json.decode(manifest_file.read())
    _manifest = data
  except Exception:
    pass


def get(name):
  return _manifest.get(name, name)
