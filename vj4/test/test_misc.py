import unittest

from vj4.util import misc


class Test(unittest.TestCase):
  def test_dedupe(self):
    self.assertListEqual(misc.dedupe([2,1,1,3,2,3]),[2,1,3])
    self.assertListEqual(misc.dedupe([]),[])
    self.assertListEqual(misc.dedupe(map(int,['2','1','1','3','2','3'])),[2,1,3])
    self.assertListEqual(misc.dedupe(['b','a','b','c','b']),['b','a','c'])
    self.assertListEqual(misc.dedupe([0]),[0])


if __name__ == '__main__':
  unittest.main()
