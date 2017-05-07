import bson

from vj4 import mq
from vj4.util import options

options.define('queue_prefetch', default=1, help='Queue prefetch count.')


async def publish(key, **kwargs):
  channel = await mq.channel('queue')
  await channel.queue_declare(key)
  await channel.basic_publish(bson.BSON.encode(kwargs), '', key)


async def consume(key, on_message):
  channel = await mq.channel()
  await channel.queue_declare(key)
  await channel.basic_qos(prefetch_count=options.queue_prefetch)
  await channel.basic_consume((lambda channel, body, envelope, properties:
                               on_message(envelope.delivery_tag, **bson.BSON.decode(body))), key)
  return channel
