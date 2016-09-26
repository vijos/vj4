import unittest

from vj4.service import smallcache
from vj4.test import base
from vj4.util import options


class OfflineTest(unittest.TestCase):
  def setUp(self):
    options.smallcache_max_entries = 4

  def tearDown(self):
    smallcache._cache.clear()

  def test_none(self):
    self.assertIsNone(smallcache.get(0))

  def test_one(self):
    smallcache.set_local(0, 7)
    self.assertEqual(smallcache.get(0), 7)

  def test_five(self):
    smallcache.set_local(0, 7)
    smallcache.set_local(1, 0)
    smallcache.set_local(2, 5)
    smallcache.set_local(3, 1)
    smallcache.set_local(4, 4)
    self.assertIsNone(smallcache.get(0))
    self.assertEqual(smallcache.get(1), 0)
    self.assertEqual(smallcache.get(2), 5)
    self.assertEqual(smallcache.get(3), 1)
    self.assertEqual(smallcache.get(4), 4)

  def test_five_access(self):
    smallcache.set_local(0, 7)
    smallcache.set_local(1, 0)
    smallcache.set_local(2, 5)
    self.assertEqual(smallcache.get(0), 7)
    smallcache.set_local(3, 1)
    smallcache.set_local(4, 4)
    self.assertEqual(smallcache.get(0), 7)
    self.assertIsNone(smallcache.get(1))
    self.assertEqual(smallcache.get(2), 5)
    self.assertEqual(smallcache.get(3), 1)
    self.assertEqual(smallcache.get(4), 4)

  def test_five_access_two(self):
    smallcache.set_local(0, 7)
    smallcache.set_local(1, 0)
    smallcache.set_local(2, 5)
    self.assertEqual(smallcache.get(0), 7)
    self.assertEqual(smallcache.get(1), 0)
    smallcache.set_local(3, 1)
    smallcache.set_local(4, 4)
    self.assertEqual(smallcache.get(0), 7)
    self.assertEqual(smallcache.get(1), 0)
    self.assertIsNone(smallcache.get(2))
    self.assertEqual(smallcache.get(3), 1)
    self.assertEqual(smallcache.get(4), 4)

  def test_five_access_three(self):
    smallcache.set_local(0, 7)
    smallcache.set_local(1, 0)
    smallcache.set_local(2, 5)
    self.assertEqual(smallcache.get(0), 7)
    self.assertEqual(smallcache.get(1), 0)
    self.assertEqual(smallcache.get(2), 5)
    smallcache.set_local(3, 1)
    smallcache.set_local(4, 4)
    self.assertIsNone(smallcache.get(0))
    self.assertEqual(smallcache.get(1), 0)
    self.assertEqual(smallcache.get(2), 5)
    self.assertEqual(smallcache.get(3), 1)
    self.assertEqual(smallcache.get(4), 4)


class OnlineTest(base.SmallcacheTestCase):
  @base.wrap_coro
  async def test_unset(self):
    smallcache.set_local(0, 7)
    await smallcache.unset_global(0)
    self.assertIsNone(smallcache.get(0))


if __name__ == '__main__':
  unittest.main()
