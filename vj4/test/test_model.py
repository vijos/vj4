import datetime
import hashlib
import time
import unittest

from bson import objectid
from gridfs import errors as gridfs_errors
from pymongo import errors as pymongo_errors

from vj4 import db
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.model import opcount
from vj4.model import system
from vj4.model import user
from vj4.test import base

CONTENT = 'dummy_content'
CONTENT2 = 'dummy_dummy'
DUP_UID = 0
DUP_UNAME = 'GuESt'
UID = 22
UNAME = 'twd2'
OWNER_UID = -1
DOMAIN_ID = 'dummy_domain'
DOMAIN_NAME = 'Dummy Domain'
DOC_TYPE = document.TYPE_PROBLEM
SUB_DOC_KEY = 'subsub'
STATUS_KEY = 'dummy_key'
FOO_ROLE = 'foo'
BAR_ROLE = 'bar'
ROLES = {FOO_ROLE: 777, BAR_ROLE: 777}
OWNER_UID2 = 222
OP1 = 'test1'
OP2 = 'test2'
IDENT = '127.0.0.1'


class SystemTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_inc_user_counter(self):
    self.assertEqual(await system.inc_user_counter(), 2)
    self.assertEqual(await system.inc_user_counter(), 3)


class UserTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_add_user(self):
    with self.assertRaises(error.UserAlreadyExistError):
      await user.add(DUP_UID, DUP_UNAME, '123456', 'dup@vijos.org')

  @base.wrap_coro
  async def test_set_password(self):
    await user.add(UID, UNAME, '123456', 'twd2@vijos.org')
    self.assertNotEqual(await user.check_password_by_uid(UID, '123456'), None)
    await user.set_password(UID, '123457')
    self.assertEqual(await user.check_password_by_uid(UID, '123456'), None)

  @base.wrap_coro
  async def test_change_password(self):
    await user.add(UID, UNAME, '123456', 'twd2@vijos.org')
    self.assertNotEqual(await user.check_password_by_uid(UID, '123456'), None)
    self.assertNotEqual(await user.change_password(UID, '123456', '123457'), None)
    self.assertEqual(await user.check_password_by_uid(UID, '123456'), None)

  @base.wrap_coro
  async def test_change_password_failed(self):
    await user.add(UID, UNAME, '123456', 'twd2@vijos.org')
    self.assertNotEqual(await user.check_password_by_uid(UID, '123456'), None)
    self.assertEqual(await user.change_password(UID, '123457', '123457'), None)
    self.assertNotEqual(await user.check_password_by_uid(UID, '123456'), None)

class DocumentTest(base.DatabaseTestCase):
  def test_convert_doc_id(self):
    doc_id = objectid.ObjectId()
    self.assertEqual(document.convert_doc_id(doc_id), doc_id)
    self.assertEqual(document.convert_doc_id(str(doc_id)), doc_id)
    self.assertEqual(document.convert_doc_id(70514), 70514)

  @base.wrap_coro
  async def test_add_get(self):
    doc_id = await document.add(DOMAIN_ID, CONTENT, OWNER_UID, DOC_TYPE)
    doc = await document.get(DOMAIN_ID, DOC_TYPE, doc_id)
    self.assertEqual(doc['_id'], doc_id)
    self.assertEqual(doc['content'], CONTENT)
    self.assertEqual(doc['owner_uid'], OWNER_UID)
    self.assertEqual(doc['domain_id'], DOMAIN_ID)
    self.assertEqual(doc['doc_type'], DOC_TYPE)
    self.assertEqual(doc['doc_id'], doc_id)
    docs = document.get_multi(domain_id=DOMAIN_ID, doc_type=DOC_TYPE, fields=['doc_id', 'title'])
    doc = await docs.__anext__()
    self.assertEqual(doc['doc_id'], doc_id)
    self.assertFalse('content' in doc)
    with self.assertRaises(StopAsyncIteration):
      await docs.__anext__()

  @base.wrap_coro
  async def test_sub_doc(self):
    doc_id = await document.add(DOMAIN_ID, CONTENT, OWNER_UID, DOC_TYPE, **{SUB_DOC_KEY: []})
    doc, sid = await document.push(DOMAIN_ID, DOC_TYPE, doc_id, SUB_DOC_KEY, CONTENT, OWNER_UID)
    self.assertEqual(doc[SUB_DOC_KEY][0]['_id'], sid)
    self.assertEqual(doc[SUB_DOC_KEY][0]['content'], CONTENT)
    self.assertEqual(doc[SUB_DOC_KEY][0]['owner_uid'], OWNER_UID)
    doc, sdoc = await document.get_sub(DOMAIN_ID, DOC_TYPE, doc_id, SUB_DOC_KEY, sid)
    self.assertEqual(sdoc['_id'], sid)
    self.assertEqual(sdoc['content'], CONTENT)
    self.assertEqual(sdoc['owner_uid'], OWNER_UID)
    doc = await document.set_sub(DOMAIN_ID, DOC_TYPE, doc_id, SUB_DOC_KEY, sid,
                                 content=CONTENT2)
    self.assertEqual(doc[SUB_DOC_KEY][0]['content'], CONTENT2)
    doc, sdoc = await document.get_sub(DOMAIN_ID, DOC_TYPE, doc_id, SUB_DOC_KEY, sid)
    self.assertEqual(sdoc['content'], CONTENT2)
    doc, sid2 = await document.push(DOMAIN_ID, DOC_TYPE, doc_id, SUB_DOC_KEY, CONTENT, OWNER_UID)
    self.assertEqual(len(doc[SUB_DOC_KEY]), 2)
    doc = await document.delete_sub(DOMAIN_ID, DOC_TYPE, doc_id, SUB_DOC_KEY, sid)
    self.assertEqual(len(doc[SUB_DOC_KEY]), 1)

  @base.wrap_coro
  async def test_capped_inc_status(self):
    doc_id = await document.add(DOMAIN_ID, CONTENT, OWNER_UID, DOC_TYPE)
    doc = await document.capped_inc_status(DOMAIN_ID, DOC_TYPE, doc_id, OWNER_UID, STATUS_KEY, 1)
    self.assertEqual(doc[STATUS_KEY], 1)
    with self.assertRaises(pymongo_errors.DuplicateKeyError):
      await document.capped_inc_status(DOMAIN_ID, DOC_TYPE, doc_id, OWNER_UID, STATUS_KEY, 1)


class DomainTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_add_get_transfer(self):
    inserted_id = await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    self.assertEqual(DOMAIN_ID, inserted_id)
    ddoc = await domain.get(DOMAIN_ID)
    self.assertEqual(ddoc['_id'], DOMAIN_ID)
    self.assertEqual(ddoc['owner_uid'], OWNER_UID)
    self.assertEqual(ddoc['roles'], ROLES)
    self.assertEqual(ddoc['name'], DOMAIN_NAME)
    ddoc = await domain.transfer(DOMAIN_ID, OWNER_UID, OWNER_UID2)
    self.assertEqual(ddoc['_id'], DOMAIN_ID)
    self.assertEqual(ddoc['owner_uid'], OWNER_UID2)
    self.assertEqual(ddoc['roles'], ROLES)
    self.assertEqual(ddoc['name'], DOMAIN_NAME)
    ddoc = await domain.transfer(DOMAIN_ID, OWNER_UID, OWNER_UID2)
    self.assertIsNone(ddoc)
    with self.assertRaises(error.DomainNotFoundError):
      await domain.get('null')

  @base.wrap_coro
  async def test_add_continue_1(self):
    # test pending inserting dudoc
    await db.coll('domain').insert_one({'_id': DOMAIN_ID,
                                        'owner_uid': OWNER_UID,
                                        'pending': True})
    await domain.add_continue(DOMAIN_ID, OWNER_UID)
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue('pending' not in ddoc)
    dudoc = await domain.get_user(DOMAIN_ID, OWNER_UID)
    self.assertEqual(dudoc['role'], builtin.ROLE_ROOT)

  @base.wrap_coro
  async def test_add_continue_2(self):
    # test pending commit ddoc
    await db.coll('domain').insert_one({'_id': DOMAIN_ID,
                                        'owner_uid': OWNER_UID,
                                        'pending': True})
    await domain.add_user_role(DOMAIN_ID, OWNER_UID, BAR_ROLE)
    await domain.add_continue(DOMAIN_ID, OWNER_UID)
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue('pending' not in ddoc)
    dudoc = await domain.get_user(DOMAIN_ID, OWNER_UID)
    self.assertEqual(dudoc['role'], BAR_ROLE)

  @base.wrap_coro
  async def test_add_continue_3(self):
    # test committed
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.set_user_role(DOMAIN_ID, OWNER_UID, FOO_ROLE)
    with self.assertRaises(error.DomainNotFoundError):
      await domain.add_continue(DOMAIN_ID, OWNER_UID)
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue('pending' not in ddoc)
    dudoc = await domain.get_user(DOMAIN_ID, OWNER_UID)
    self.assertEqual(dudoc['role'], FOO_ROLE)

  @base.wrap_coro
  async def test_user_domain_account(self):
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.set_user(DOMAIN_ID, UID, test_field='test tset', num=1)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['num'], 1)
    dudoc = await domain.inc_user(DOMAIN_ID, UID, num=2)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['num'], 3)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['num'], 3)

  @base.wrap_coro
  async def test_user_domain_account_projection(self):
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.set_user(DOMAIN_ID, UID, test_field='test tset', num=1)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['num'], 1)
    dudoc = await domain.inc_user(DOMAIN_ID, UID, num=2)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['num'], 3)
    dudoc = await domain.get_user(DOMAIN_ID, UID, fields={'test_field': 0})
    self.assertTrue('test_field' not in dudoc)
    self.assertEqual(dudoc['num'], 3)

  @base.wrap_coro
  async def test_add_user_role_1(self):
    # test non-existing dudoc
    NOW = datetime.datetime.utcnow().replace(microsecond=0)
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.add_user_role(DOMAIN_ID, UID, FOO_ROLE, NOW)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['role'], FOO_ROLE)
    self.assertEqual(dudoc['join_at'], NOW)

  @base.wrap_coro
  async def test_add_user_role_2(self):
    # test existing dudoc without a role
    NOW = datetime.datetime.utcnow().replace(microsecond=0)
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.set_user(DOMAIN_ID, UID, test_field='test tset')
    await domain.add_user_role(DOMAIN_ID, UID, FOO_ROLE, NOW)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['role'], FOO_ROLE)
    self.assertEqual(dudoc['join_at'], NOW)

  @base.wrap_coro
  async def test_add_user_role_3(self):
    # test existing dudoc with a role, without join_at
    NOW = datetime.datetime.utcnow().replace(microsecond=0)
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.set_user(DOMAIN_ID, UID, test_field='test tset', role=BAR_ROLE)
    with self.assertRaises(error.UserAlreadyDomainMemberError):
      await domain.add_user_role(DOMAIN_ID, UID, FOO_ROLE, NOW)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['role'], BAR_ROLE)
    self.assertTrue('join_at' not in dudoc)

  @base.wrap_coro
  async def test_add_user_role_4(self):
    # test existing dudoc with a role and join_at
    NOW = datetime.datetime.utcnow().replace(microsecond=0)
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES, name=DOMAIN_NAME)
    await domain.set_user(DOMAIN_ID, UID, test_field='test tset', role=BAR_ROLE, join_at=NOW)
    with self.assertRaises(error.UserAlreadyDomainMemberError):
      await domain.add_user_role(DOMAIN_ID, UID, FOO_ROLE, NOW + datetime.timedelta(seconds=5))
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['test_field'], 'test tset')
    self.assertEqual(dudoc['role'], BAR_ROLE)
    self.assertEqual(dudoc['join_at'], NOW)

  @base.wrap_coro
  async def test_set_roles_1(self):
    # modify a modifiable built-in role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    await domain.set_roles(DOMAIN_ID, {builtin.ROLE_DEFAULT: 777})
    ddoc = await domain.get(DOMAIN_ID)
    self.assertEqual(ddoc['roles'][builtin.ROLE_DEFAULT], 777)

  @base.wrap_coro
  async def test_set_roles_2(self):
    # modify an non-modifiable built-in role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    with self.assertRaises(error.ModifyBuiltinRoleError):
      await domain.set_roles(DOMAIN_ID, {builtin.ROLE_ROOT: 777})
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue(builtin.ROLE_ROOT not in ddoc['roles'])

  @base.wrap_coro
  async def test_set_roles_3(self):
    # modify a non-exist role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    await domain.set_roles(DOMAIN_ID, {FOO_ROLE: 777})
    ddoc = await domain.get(DOMAIN_ID)
    self.assertEqual(ddoc['roles'][FOO_ROLE], 777)

  @base.wrap_coro
  async def test_set_roles_4(self):
    # modify an existing role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    await domain.set_roles(DOMAIN_ID, {FOO_ROLE: 777})
    await domain.set_roles(DOMAIN_ID, {FOO_ROLE: 666})
    ddoc = await domain.get(DOMAIN_ID)
    self.assertEqual(ddoc['roles'][FOO_ROLE], 666)

  @base.wrap_coro
  async def test_delete_roles_1(self):
    # delete a built-in role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    with self.assertRaises(error.ModifyBuiltinRoleError):
      await domain.delete_roles(DOMAIN_ID, [builtin.ROLE_DEFAULT])
    ddoc = await domain.get(DOMAIN_ID)
    self.assertEqual(ddoc['roles'][builtin.ROLE_DEFAULT],
                     builtin.BUILTIN_ROLE_DESCRIPTORS[builtin.ROLE_DEFAULT].default_permission)
    with self.assertRaises(error.ModifyBuiltinRoleError):
      await domain.delete_roles(DOMAIN_ID, [builtin.ROLE_ROOT])
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue(builtin.ROLE_ROOT not in ddoc['roles'])

  @base.wrap_coro
  async def test_delete_roles_2(self):
    # delete a non-existing role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    await domain.delete_roles(DOMAIN_ID, [FOO_ROLE])
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue(FOO_ROLE not in ddoc['roles'])

  @base.wrap_coro
  async def test_delete_roles_3(self):
    # delete an existing role
    await domain.add(DOMAIN_ID, OWNER_UID, name=DOMAIN_NAME)
    await domain.set_roles(DOMAIN_ID, {FOO_ROLE: 777, BAR_ROLE: 666})
    await domain.delete_roles(DOMAIN_ID, [FOO_ROLE])
    ddoc = await domain.get(DOMAIN_ID)
    self.assertTrue(FOO_ROLE not in ddoc['roles'])
    self.assertEqual(ddoc['roles'][BAR_ROLE], 666)


class FsTest(base.DatabaseTestCase):
  CONTENT = b'dummy_content'
  CONTENT_MD5 = hashlib.md5(CONTENT).hexdigest()
  SECRET = 'dummy_secret'

  @base.wrap_coro
  async def test(self):
    grid_in = await fs.add('application/octet-stream')
    await grid_in.write(self.CONTENT)
    await grid_in.close()
    file_id = grid_in._id
    grid_out = await fs.get(file_id)
    content = await grid_out.read()
    self.assertEqual(content, self.CONTENT)
    md5 = await fs.get_md5(file_id)
    self.assertEqual(md5, self.CONTENT_MD5)
    file_id_2 = await fs.link_by_md5(md5)
    self.assertEqual(file_id, file_id_2)
    await fs.unlink(file_id)
    self.assertTrue(await fs.get(file_id))
    await fs.unlink(file_id)
    with self.assertRaises(gridfs_errors.NoFile):
      await fs.get(file_id)

  @base.wrap_coro
  async def test_secret(self):
    fid = await fs.add_data('application/octet-stream', self.CONTENT)
    secret = await fs.get_secret(fid)
    fid2 = await fs.get_file_id(secret)
    self.assertEqual(fid, fid2)
    grid_out = await fs.get_by_secret(secret)
    content = await grid_out.read()
    self.assertEqual(content, self.CONTENT)
    await fs.unlink(fid)
    with self.assertRaises(error.NotFoundError):
      await fs.get_by_secret(secret)
    self.assertEqual(bool(await fs.get_file_id(secret)), False)


class OpcountTest(base.DatabaseTestCase):
  def setUp(self):
    super().setUp()
    self.old_time = time.time
    time.time = lambda: 0

  def tearDown(self):
    time.time = self.old_time
    super().tearDown()

  @base.wrap_coro
  async def test_inc(self):
    await opcount.inc(OP1, IDENT, 1, 1)
    await opcount.inc(OP2, IDENT, 1, 2)
    with self.assertRaises(error.OpcountExceededError):
      await opcount.inc(OP1, IDENT, 1, 1)
    await opcount.inc(OP2, IDENT, 1, 2)
    with self.assertRaises(error.OpcountExceededError):
      await opcount.inc(OP2, IDENT, 1, 2)
    time.time = lambda: 1
    await opcount.inc(OP1, IDENT, 1, 1)
    await opcount.inc(OP2, IDENT, 1, 2)


if __name__ == '__main__':
  unittest.main()
