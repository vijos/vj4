import hashlib
import unittest
from bson import objectid
from gridfs import errors as gridfs_errors
from pymongo import errors as pymongo_errors
from vj4 import error
from vj4.model import document
from vj4.model import fs
from vj4.model import system
from vj4.model import user
from vj4.model import domain
from vj4.test import base

CONTENT = 'dummy_content'
DUP_UID = 0
DUP_UNAME = 'GuESt'
OWNER_UID = 22
DOMAIN_ID = 'dummy_domain'
DOC_TYPE = document.TYPE_PROBLEM
STATUS_KEY = 'dummy_key'
ROLES = {'dummy': 777}
OWNER_UID2 = 222

class SystemTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_inc_user_counter(self):
    self.assertEqual(await system.inc_user_counter(), 2)
    self.assertEqual(await system.inc_user_counter(), 3)

class UserTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_add_user(self):
    with self.assertRaises(error.UserAlreadyExistError):
      await user.add(DUP_UID, DUP_UNAME, '123456', 'dup@vijos.org', 0)

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
    docs = document.get_multi(DOMAIN_ID, DOC_TYPE, fields=['doc_id', 'title'])
    doc = await docs.__anext__()
    self.assertEqual(doc['doc_id'], doc_id)
    self.assertFalse('content' in doc)
    with self.assertRaises(StopAsyncIteration):
      await docs.__anext__()

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
    await domain.add(DOMAIN_ID, OWNER_UID, ROLES)
    ddoc = await domain.get(DOMAIN_ID)
    self.assertEqual(ddoc['_id'], DOMAIN_ID)
    self.assertEqual(ddoc['owner_uid'], OWNER_UID)
    self.assertEqual(ddoc['roles'], ROLES)
    ddoc = await domain.transfer(DOMAIN_ID, OWNER_UID, OWNER_UID2)
    self.assertEqual(ddoc['_id'], DOMAIN_ID)
    self.assertEqual(ddoc['owner_uid'], OWNER_UID2)
    self.assertEqual(ddoc['roles'], ROLES)
    ddoc = await domain.transfer(DOMAIN_ID, OWNER_UID, OWNER_UID2)
    self.assertIsNone(ddoc)
    ddoc = await domain.get('null')
    self.assertIsNone(ddoc)

class FsTest(base.DatabaseTestCase):
  CONTENT = b'dummy_content'
  CONTENT_MD5 = hashlib.md5(CONTENT).hexdigest()

  @base.wrap_coro
  async def test(self):
    grid_in = await fs.add()
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

if __name__ == '__main__':
  unittest.main()
