import time
import watchdog

from os import path
from vj4.util import json
from watchdog.observers import Observer

MANIFEST_FILE = 'static-manifest.json'
_manifest_dir = None
_manifest_path = None
_manifest = {}


def init(static_dir):
  global _manifest_dir, _manifest_path
  _manifest_dir = static_dir
  _manifest_path = path.join(_manifest_dir, MANIFEST_FILE)
  update()
  watch()

def update():
  global _manifest
  try:
    with open(_manifest_path, 'r') as manifest_file:
      data = json.decode(manifest_file.read())
    _manifest = data
  except Exception as e:
    pass

def watch():
  handler = ManifestChangeHandler()
  observer = watchdog.observers.Observer()
  observer.schedule(handler, _manifest_dir)
  observer.start()

def get(name):
  return _manifest.get(name, name)


class ManifestChangeHandler(watchdog.events.FileSystemEventHandler):
  def on_modified(self, event):
    if event.src_path == _manifest_path:
      time.sleep(1)
      update()
