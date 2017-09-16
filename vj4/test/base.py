import asyncio
import functools
import os
import unittest

import pymongo

from vj4 import db
from vj4.service import bus
from vj4.service import event
from vj4.service import queue
from vj4.service import smallcache
from vj4.util import options
from vj4.util import tools

wait = asyncio.get_event_loop().run_until_complete


class DatabaseTestCase(unittest.TestCase):
  def setUp(self):
    db._client = None
    db._db = None
    db.coll.cache_clear()
    db.fs.cache_clear()
    options.db_name = 'unittest_' + str(os.getpid())
    wait(db.init())
    wait(tools.ensure_all_indexes())

  def tearDown(self):
    db._client.close()
    wait(db._client.wait_closed())
    pymongo.MongoClient(options.db_host).drop_database(options.db_name)


class BusTestCase(DatabaseTestCase):
  def setUp(self):
    super(BusTestCase, self).setUp()
    self.old_publish = bus.publish
    bus.publish = event.publish
    self.old_subscribe = bus.subscribe
    bus.subscribe = event.subscribe
    self.old_unsubscribe = bus.unsubscribe
    bus.unsubscribe = event.unsubscribe

  def tearDown(self):
    bus.publish = self.old_publish
    bus.subscribe = self.old_subscribe
    bus.unsubscribe = self.old_unsubscribe
    super(BusTestCase, self).tearDown()


class QueueTestCase(DatabaseTestCase):
  async def noop(*args, **kwargs):
    pass

  def setUp(self):
    super(QueueTestCase, self).setUp()
    self.old_publish = queue.publish
    queue.publish = QueueTestCase.noop
    self.old_consume = queue.consume
    queue.consume = QueueTestCase.noop

  def tearDown(self):
    queue.publish = self.old_publish
    queue.consume = self.old_consume
    super(QueueTestCase, self).tearDown()


class SmallcacheTestCase(BusTestCase):
  def setUp(self):
    super(SmallcacheTestCase, self).setUp()
    smallcache.init()

  def tearDown(self):
    smallcache.uninit()
    super(SmallcacheTestCase, self).tearDown()


def wrap_coro(coro):
  @functools.wraps(coro)
  def wrapped(*args, **kwargs):
    wait(coro(*args, **kwargs))

  return wrapped
