import unittest

from vj4.util import validator


class Test(unittest.TestCase):
  def test_uid(self):
    self.assertTrue(validator.is_uid('123'))
    self.assertTrue(validator.is_uid('-456'))
    self.assertFalse(validator.is_uid(''))
    self.assertFalse(validator.is_uid('1.23'))
    self.assertFalse(validator.is_uid('xyz'))

  def test_uname(self):
    self.assertTrue(validator.is_uname('twd2'))
    self.assertTrue(validator.is_uname('123twd3'))
    self.assertTrue(validator.is_uname('$%1234'))
    self.assertTrue(validator.is_uname('12<><?,.,./,.,.;\'\'[] 3   t  ###2$%^&&*%&#^%$@#$^wd3'))
    self.assertTrue(validator.is_uname('中文测试'))
    self.assertTrue(validator.is_uname('twd' * 10))
    self.assertFalse(validator.is_uname(''))
    self.assertFalse(validator.is_uname(' twd4'))
    self.assertFalse(validator.is_uname('twd4\u3000'))
    self.assertFalse(validator.is_uname('twd' * 500))
    self.assertFalse(validator.is_uname('\ntwd4'))

  def test_password(self):
    self.assertTrue(validator.is_password('123twd3'))
    self.assertTrue(validator.is_password('12<><?,.,./,.,.;\'\'[]_+)}_+{}{\\%^^%$@#$^wd3'))
    self.assertTrue(validator.is_password(' twd4'))
    self.assertTrue(validator.is_password('twd4\u3000'))
    self.assertTrue(validator.is_password('twd' * 10))
    self.assertTrue(validator.is_password('twd' * 500))
    self.assertFalse(validator.is_password('twd2'))
    self.assertFalse(validator.is_password(''))

  def test_mail(self):
    self.assertTrue(validator.is_mail('ex@example.com'))
    self.assertTrue(validator.is_mail('1+e-x@example.com'))
    self.assertTrue(validator.is_mail('example.net@example.com'))
    self.assertFalse(validator.is_mail('example:net@example.com'))
    self.assertFalse(validator.is_mail('ex@examplecom'))
    self.assertFalse(validator.is_mail('example.com'))
    self.assertFalse(validator.is_mail('examplecom'))
    self.assertFalse(validator.is_mail('1+e=x@example.com'))

  def test_domain_id(self):
    self.assertTrue(validator.is_domain_id('my_domain_1'))
    self.assertTrue(validator.is_domain_id('My_Domain'))
    self.assertTrue(validator.is_domain_id('MyDomain'))
    self.assertTrue(validator.is_domain_id('myDomain'))
    self.assertTrue(validator.is_domain_id('twd2'))
    self.assertTrue(validator.is_domain_id('twd' * 10))
    self.assertFalse(validator.is_domain_id('C:\\a.txt'))
    self.assertFalse(validator.is_domain_id('/etc/hosts'))
    self.assertFalse(validator.is_domain_id(''))
    self.assertFalse(validator.is_domain_id(' twd4'))
    self.assertFalse(validator.is_domain_id('twd4\u3000'))
    self.assertFalse(validator.is_domain_id('\ntwd4'))
    self.assertFalse(validator.is_domain_id('22domain'))
    self.assertFalse(validator.is_domain_id('22-Domain'))
    self.assertFalse(validator.is_domain_id('My-Domain'))
    self.assertFalse(validator.is_domain_id('dom'))
    self.assertFalse(validator.is_domain_id('twd' * 500))
    self.assertFalse(validator.is_domain_id('twd\r\n2'))
    self.assertFalse(validator.is_domain_id('$domain'))
    self.assertFalse(validator.is_domain_id('12<><?,.,./,.,.;\'\'[] 3   t  ###2$%^&&*%&#^'))
    self.assertFalse(validator.is_domain_id('domain.id'))

  def test_id(self):
    self.assertTrue(validator.is_id('my_domain_1'))
    self.assertTrue(validator.is_id('My_Domain'))
    self.assertTrue(validator.is_id('MyDomain'))
    self.assertTrue(validator.is_id('myDomain'))
    self.assertTrue(validator.is_id('twd2'))
    self.assertTrue(validator.is_id('twd' * 10))
    self.assertTrue(validator.is_id('$node'))
    self.assertTrue(validator.is_id('标识符'))
    self.assertTrue(validator.is_id('22-ident'))
    self.assertTrue(validator.is_id('My-Domain'))
    self.assertTrue(validator.is_id('dom'))
    self.assertTrue(validator.is_id('twd' * 500))
    self.assertTrue(validator.is_id('user.ident'))
    self.assertFalse(validator.is_id('C:\\a.txt'))
    self.assertFalse(validator.is_id('/etc/hosts'))
    self.assertFalse(validator.is_id(''))
    self.assertFalse(validator.is_id(' twd4'))
    self.assertFalse(validator.is_id('twd4\u3000'))
    self.assertFalse(validator.is_id('\ntwd4'))
    self.assertFalse(validator.is_id('12<><?,.,./,.,.;\'\'[] 3   t  ###2$%^&&*%&#^'))

  def test_role(self):
    self.assertTrue(validator.is_role('my_domain_1'))
    self.assertTrue(validator.is_role('My_Domain'))
    self.assertTrue(validator.is_role('MyDomain'))
    self.assertTrue(validator.is_role('myDomain'))
    self.assertTrue(validator.is_role('twd2'))
    self.assertTrue(validator.is_role('twd' * 10))
    self.assertTrue(validator.is_role('r0le'))
    self.assertTrue(validator.is_role('1role'))
    self.assertFalse(validator.is_role('C:\\a.txt'))
    self.assertFalse(validator.is_role('/etc/hosts'))
    self.assertFalse(validator.is_role(''))
    self.assertFalse(validator.is_role(' twd4'))
    self.assertFalse(validator.is_role('twd4\u3000'))
    self.assertFalse(validator.is_role('\ntwd4'))
    self.assertFalse(validator.is_role('My-Role'))
    self.assertFalse(validator.is_role('twd' * 90))
    self.assertFalse(validator.is_role('twd\r\n2'))
    self.assertFalse(validator.is_role('$role'))
    self.assertFalse(validator.is_role('role.admin'))
    self.assertFalse(validator.is_role('12<><?,.,./,.,.;\'\'[#2$%^&&*%&#^'))

  def test_name(self):
    self.assertTrue(validator.is_name('dummy_name'))
    self.assertFalse(validator.is_name(''))
    self.assertFalse(validator.is_name('x' * 300))

  def test_content(self):
    self.assertTrue(validator.is_content('dummy_name'))
    self.assertTrue(validator.is_content('x' * 300))
    self.assertFalse(validator.is_content(''))
    self.assertTrue(validator.is_content('c'))
    self.assertFalse(validator.is_content('x' * 700000))

  def test_intro(self):
    self.assertTrue(validator.is_intro('d'))
    self.assertTrue(validator.is_intro('dummy_name'))
    self.assertTrue(validator.is_intro('x' * 300))
    self.assertFalse(validator.is_intro(''))
    self.assertFalse(validator.is_intro('g' * 501))
    self.assertFalse(validator.is_intro('x' * 700000))

  def test_description(self):
    self.assertTrue(validator.is_description('d'))
    self.assertTrue(validator.is_description('dummy_name'))
    self.assertTrue(validator.is_description('x' * 300))
    self.assertTrue(validator.is_description(''))
    self.assertFalse(validator.is_description('x' * 700000))

  def test_domain_invitation_code(self):
    self.assertTrue(validator.is_domain_invitation_code('helloworld'))
    self.assertFalse(validator.is_domain_invitation_code(''))


if __name__ == '__main__':
  unittest.main()
