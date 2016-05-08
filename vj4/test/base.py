import asyncio
import functools
import os
import pymongo
import unittest
from vj4 import db
from vj4.controller import smallcache
from vj4.model import bus
from vj4.util import event
from vj4.util import options
from vj4.util import tools

wait = asyncio.get_event_loop().run_until_complete

class DatabaseTestCase(unittest.TestCase):
  def setUp(self):
    db.Database._instance, db.Collection._instances, db.GridFS._instances = None, {}, {}
    options.options.db_name = 'unittest_' + str(os.getpid())
    wait(tools.ensure_all_indexes())

  def tearDown(self):
    pymongo.MongoClient(options.options.db_host).drop_database(options.options.db_name)

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
