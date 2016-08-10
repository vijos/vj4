"""Helper module which implements the event listener module.

Events are only published to subscribers in the same process, which is different from vj4.model.bus,
which broadcasts events to all processes connected to the database.
"""
import asyncio

from vj4.util import argmethod

_subscribers = {}


async def publish(key, value):
  coroutines = [subscriber({'key': key, 'value': value})
                for subscriber, key_set in _subscribers.items()
                if key in key_set]
  await asyncio.gather(*coroutines)


def subscribe(callback, keys):
  """Subscibe a set of event keys for a callback.

  Args:
    callback: coroutine function for event callback.
    keys: list, set or tuple of object for event keys.
  """
  assert type(keys) in (set, list, tuple)
  _subscribers[callback] = keys


def unsubscribe(callback):
  """Unsubscribe events for a callback.

  Args:
    callback: coroutine function for event callback.
  """
  if callback in _subscribers:
    del _subscribers[callback]


def subscribes(keys):
  assert type(keys) in (set, list, tuple)

  def decorator(callback):
    subscribe(callback, keys)
    return callback

  return decorator


if __name__ == '__main__':
  argmethod.invoke_by_args()
