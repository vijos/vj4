import unittest

from vj4.util import pwhash


class Test(unittest.TestCase):
  def test_gen_salt(self):
    salt1 = pwhash.gen_salt()
    self.assertEqual(len(salt1), 40)
    salt2 = pwhash.gen_salt()
    self.assertNotEqual(salt1, salt2)
    salt3 = pwhash.gen_salt(16)
    self.assertEqual(len(salt3), 32)

  def test_hash_check_vj2(self):
    password1 = 'password1'
    salt1 = pwhash.gen_salt()
    hash1 = pwhash.hash_vj2('icebox', password1, salt1)
    self.assertTrue(pwhash.check(password1, salt1, hash1))
    salt2 = pwhash.gen_salt()
    self.assertFalse(pwhash.check(password1, salt2, hash1))
    password2 = 'password2'
    self.assertFalse(pwhash.check(password2, salt1, hash1))

  def test_hash_check_vj4(self):
    password1 = 'password1'
    salt1 = pwhash.gen_salt()
    hash1 = pwhash.hash_vj4(password1, salt1)
    self.assertTrue(pwhash.check(password1, salt1, hash1))
    salt2 = pwhash.gen_salt()
    self.assertFalse(pwhash.check(password1, salt2, hash1))
    password2 = 'password2'
    self.assertFalse(pwhash.check(password2, salt1, hash1))


if __name__ == '__main__':
  unittest.main()
