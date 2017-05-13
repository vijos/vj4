import unittest
from bson import objectid

from vj4 import error
from vj4.model import document
from vj4.model.adaptor import discussion
from vj4.test import base

DOMAIN_ID_DUMMY = 'dummy'
OWNER_UID = 22
TITLE = 'dummy_title'
CONTENT = 'dummy_content'
REPLY_CONTENT = 'dummy_reply'

class NodesTest(base.SmallcacheTestCase):
  @base.wrap_coro
  async def test_none(self):
    nodes = await discussion.get_nodes(DOMAIN_ID_DUMMY)
    self.assertDictEqual(nodes, {})

  @base.wrap_coro
  async def test_one_category(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    nodes = await discussion.get_nodes(DOMAIN_ID_DUMMY)
    self.assertDictEqual(nodes, {'cat': []})

  @base.wrap_coro
  async def test_two_categories(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_category(DOMAIN_ID_DUMMY, 'dog')
    nodes = await discussion.get_nodes(DOMAIN_ID_DUMMY)
    self.assertDictEqual(nodes, {'cat': [], 'dog': []})

  @base.wrap_coro
  async def test_duplicate_category(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    with self.assertRaises(error.DiscussionCategoryAlreadyExistError):
      await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')

  @base.wrap_coro
  async def test_one_node(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    nodes = await discussion.get_nodes(DOMAIN_ID_DUMMY)
    self.assertDictEqual(nodes, {'cat': [{'name': 'meow', 'pic': None}]})

  @base.wrap_coro
  async def test_two_nodes(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'yowl')
    nodes = await discussion.get_nodes(DOMAIN_ID_DUMMY)
    self.assertDictEqual(nodes, {'cat': [{'name': 'meow', 'pic': None}, {'name': 'yowl', 'pic': None}]})

  @base.wrap_coro
  async def test_duplicate_node(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    with self.assertRaises(error.DiscussionNodeAlreadyExistError):
      await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')

  @base.wrap_coro
  async def test_separate_two_nodes(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    await discussion.add_category(DOMAIN_ID_DUMMY, 'dog')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'dog', 'woof')
    nodes = await discussion.get_nodes(DOMAIN_ID_DUMMY)
    self.assertDictEqual(nodes, {'cat': [{'name': 'meow', 'pic': None}], 'dog': [{'name': 'woof', 'pic': None}]})

  @base.wrap_coro
  async def test_separate_duplicate_node(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    await discussion.add_category(DOMAIN_ID_DUMMY, 'dog')
    with self.assertRaises(error.DiscussionNodeAlreadyExistError):
      await discussion.add_node(DOMAIN_ID_DUMMY, 'dog', 'meow')

  @base.wrap_coro
  async def test_category_not_found(self):
    with self.assertRaises(error.DiscussionCategoryNotFoundError):
      await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')

  @base.wrap_coro
  async def test_node_not_found(self):
    with self.assertRaises(error.DiscussionNodeNotFoundError):
      await discussion.check_node(DOMAIN_ID_DUMMY, 'meow')


class DiscussionTest(base.SmallcacheTestCase):
  @base.wrap_coro
  async def test_add_get(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    vnode = await discussion.get_vnode(DOMAIN_ID_DUMMY, 'meow')
    ddocs = await discussion.get_multi(DOMAIN_ID_DUMMY,
                                       parent_doc_type=vnode['doc_type'],
                                       parent_doc_id=vnode['doc_id']).to_list()
    self.assertEqual(len(ddocs), 0)
    did = await discussion.add(DOMAIN_ID_DUMMY, 'meow', OWNER_UID, TITLE, CONTENT)
    ddoc = await discussion.get(DOMAIN_ID_DUMMY, did)
    self.assertEqual(ddoc['doc_id'], did)
    self.assertEqual(ddoc['domain_id'], DOMAIN_ID_DUMMY)
    self.assertEqual(ddoc['parent_doc_type'], document.TYPE_DISCUSSION_NODE)
    self.assertEqual(ddoc['parent_doc_id'], 'meow')
    self.assertEqual(ddoc['owner_uid'], OWNER_UID)
    self.assertEqual(ddoc['title'], TITLE)
    self.assertEqual(ddoc['content'], CONTENT)
    vnode = await discussion.get_vnode(DOMAIN_ID_DUMMY, 'meow')
    ddocs = await discussion.get_multi(DOMAIN_ID_DUMMY,
                                       parent_doc_type=vnode['doc_type'],
                                       parent_doc_id=vnode['doc_id'],
                                       fields=['title',
                                               'owner_uid',
                                               'parent_doc_id']).to_list()
    self.assertEqual(len(ddocs), 1)
    self.assertEqual(ddocs[0]['title'], TITLE)
    self.assertFalse('content' in ddocs[0])

  @base.wrap_coro
  async def test_reply_add_get_del(self):
    await discussion.add_category(DOMAIN_ID_DUMMY, 'cat')
    await discussion.add_node(DOMAIN_ID_DUMMY, 'cat', 'meow')
    vnode = await discussion.get_vnode(DOMAIN_ID_DUMMY, 'meow')
    ddocs = await discussion.get_multi(DOMAIN_ID_DUMMY,
                                       parent_doc_type=vnode['doc_type'],
                                       parent_doc_id=vnode['doc_id']).to_list()
    self.assertEqual(len(ddocs), 0)
    did = await discussion.add(DOMAIN_ID_DUMMY, 'meow', OWNER_UID, TITLE, CONTENT)
    drid = await discussion.add_reply(DOMAIN_ID_DUMMY, did, OWNER_UID, REPLY_CONTENT)
    ddoc = await discussion.get(DOMAIN_ID_DUMMY, did)
    self.assertEqual(ddoc['num_replies'], 1)
    drdoc = await discussion.get_reply(DOMAIN_ID_DUMMY, drid, did)
    self.assertEqual(drdoc['doc_id'], drid)
    self.assertEqual(drdoc['domain_id'], DOMAIN_ID_DUMMY)
    self.assertEqual(drdoc['parent_doc_type'], document.TYPE_DISCUSSION)
    self.assertEqual(drdoc['parent_doc_id'], did)
    self.assertEqual(drdoc['owner_uid'], OWNER_UID)
    self.assertEqual(drdoc['content'], REPLY_CONTENT)
    with self.assertRaises(error.DocumentNotFoundError):
      await discussion.delete_reply(DOMAIN_ID_DUMMY, objectid.ObjectId('0' * 24))
    ddoc = await discussion.get(DOMAIN_ID_DUMMY, did)
    self.assertEqual(ddoc['num_replies'], 1)
    self.assertTrue(await discussion.delete_reply(DOMAIN_ID_DUMMY, drid))
    with self.assertRaises(error.DocumentNotFoundError):
      await discussion.get_reply(DOMAIN_ID_DUMMY, drid, did)
    ddoc = await discussion.get(DOMAIN_ID_DUMMY, did)
    self.assertEqual(ddoc['num_replies'], 0)


if __name__ == '__main__':
  unittest.main()
