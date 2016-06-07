import unittest

from vj4.handler import base

PERM_DUMMY = 1
PRIV_DUMMY = 2


class DummyHandler(object):
  def __init__(self):
    self.perm_checked = None
    self.priv_checked = None

  def check_perm(self, perm):
    self.perm_checked = perm

  def check_priv(self, priv):
    self.priv_checked = priv


class DecoratorTest(unittest.TestCase, DummyHandler):
  def setUp(self):
    DummyHandler.__init__(self)

  @base.require_perm(PERM_DUMMY)
  def assert_perm_checked(self, perm):
    self.assertEqual(self.perm_checked, perm)

  @base.require_priv(PRIV_DUMMY)
  def assert_priv_checked(self, priv):
    self.assertEqual(self.priv_checked, priv)

  def test_require_perm_func(self):
    self.assertIsNone(self.perm_checked)
    self.assert_perm_checked(PERM_DUMMY)

  def test_require_priv_func(self):
    self.assertIsNone(self.priv_checked)
    self.assert_priv_checked(PRIV_DUMMY)


if __name__ == '__main__':
  unittest.main()
