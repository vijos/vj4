import collections
import copy

from vj4.service import bus
from vj4.util import options

PREFIX_DISCUSSION_NODES = 'discussion-nodes-'

options.define('smallcache_max_entries', default=64,
               help='Maximum number of entries in smallcache.')

_cache = collections.OrderedDict()


async def _on_unset(e):
  if e['value'] in _cache:
    del _cache[e['value']]


def init():
  bus.subscribe(_on_unset, ['smallcache-unset'])


def get_direct(key, default=None):
  if key not in _cache:
    return default
  _cache.move_to_end(key)
  return _cache[key]


def get(key, default=None):
  return copy.deepcopy(get_direct(key, default))


def set_local_direct(key, value):
  if key in _cache:
    del _cache[key]
  _cache[key] = value
  if len(_cache) > options.smallcache_max_entries:
    _cache.popitem(False)


def set_local(key, value):
  set_local_direct(key, copy.deepcopy(value))


async def unset_global(key):
  await bus.publish('smallcache-unset', key)


def uninit():
  bus.unsubscribe(_on_unset)
  _cache.clear()
