import asyncio
import logging
import pprint

import bson

from vj4 import mq
from vj4.util import argmethod

_logger = logging.getLogger(__name__)
_subscribers = dict()
_throttles = dict()


async def init():
  channel = await _consume()
  asyncio.get_event_loop().create_task(_work(channel))


async def _consume():
  channel = await mq.channel('bus')
  await channel.exchange_declare('bus', 'fanout', auto_delete=True)
  queue = await channel.queue_declare(exclusive=True, auto_delete=True)
  queue_name = queue['queue']
  await channel.queue_bind(queue_name, 'bus', '')

  async def on_message(channel, body, envelope, properties):
    e = bson.BSON.decode(body)
    coroutines = [subscriber(e)
                  for subscriber, key_set in _subscribers.items()
                  if e['key'] in key_set]
    await asyncio.gather(*coroutines)

  await channel.basic_consume(on_message, queue_name)
  return channel


async def _work(channel):
  while True:
    await channel.close_event.wait()
    _logger.warning('Message queue channel died, waiting for retry.')
    await asyncio.sleep(2)
    try:
      channel = await _consume()
    except Exception as e:
      _logger.exception(e)


@argmethod.wrap
async def publish(key: str, value: str):
  channel = await mq.channel('bus')
  await channel.basic_publish(bson.BSON.encode({'key': key, 'value': value}), 'bus', '')


def publish_throttle(key, value, throttle_id, delay=.016):
  loop = asyncio.get_event_loop()
  if throttle_id not in _throttles:
    loop.call_later(delay, lambda: loop.create_task(publish(key, _throttles.pop(throttle_id))))
  _throttles[throttle_id] = value


def subscribe(callback, keys):
  """Subscibe a set of bus keys for a callback.

  Args:
    callback: coroutine function for bus callback.
    keys: list, set or tuple of object for event keys.
  """
  assert type(keys) in (set, list, tuple)
  _subscribers[callback] = keys


def unsubscribe(callback):
  """Unsubscribe buses for a callback.

  Args:
    callback: coroutine function for bus callback.
  """
  if callback in _subscribers:
    del _subscribers[callback]


@argmethod.wrap
async def tail():
  channel = await mq.channel('bus')
  await channel.exchange_declare('bus', 'fanout', auto_delete=True)
  queue = await channel.queue_declare(exclusive=True, auto_delete=True)
  queue_name = queue['queue']
  await channel.queue_bind(queue_name, 'bus', '')

  async def on_message(channel, body, envelope, properties):
    pprint.pprint(bson.BSON.decode(body))

  await channel.basic_consume(on_message, queue_name)
  await channel.close_event.wait()


if __name__ == '__main__':
  argmethod.invoke_by_args()
