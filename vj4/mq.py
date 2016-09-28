import asyncio

import aioamqp

from vj4.util import options

options.define('mq_host', default='localhost', help='Message queue hostname or IP address.')
options.define('mq_vhost', default='/', help='Message queue virtual host.')

_protocol_future = None
_channel_futures = {}


async def _connect():
  global _protocol_future
  if _protocol_future:
    return await _protocol_future
  _protocol_future = future = asyncio.Future()
  try:
    _, protocol = await aioamqp.connect(host=options.mq_host, virtualhost=options.mq_vhost)
    future.set_result(protocol)
    asyncio.get_event_loop().create_task(_wait_protocol(protocol))
    return protocol
  except Exception as e:
    future.set_exception(e)
    _protocol_future = None
    raise


async def _wait_protocol(protocol):
  global _protocol_future
  await protocol.wait_closed()
  _protocol_future = None


async def channel(key=None):
  global _channel_futures
  if key:
    if key in _channel_futures:
      return await _channel_futures[key]
    future = asyncio.Future()
    _channel_futures[key] = future
  try:
    channel = await (await _connect()).channel()
    if key:
      future.set_result(channel)
      asyncio.get_event_loop().create_task(_wait_channel(channel, key))
    return channel
  except Exception as e:
    future.set_exception(e)
    del _channel_futures[key]
    raise


async def _wait_channel(channel, key):
  global _channel_futures
  await channel.close_event.wait()
  del _channel_futures[key]
