import unittest

from vj4 import error
from vj4.model.adaptor import problem
from vj4.test import base

DOMAIN_ID = 'dummy_domain'
TITLE = 'dummy_title'
CONTENT = 'dummy_content'
UID = 22
PID = 777
CONTENT2 = 'dummy_content2'
UID2 = 222


class ProblemTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_add_get(self):
    pid = await problem.add(DOMAIN_ID, TITLE, CONTENT, UID, PID)
    self.assertEqual(pid, PID)
    pdoc = await problem.get(DOMAIN_ID, pid)
    self.assertEqual(pdoc['domain_id'], DOMAIN_ID)
    self.assertEqual(pdoc['title'], TITLE)
    self.assertEqual(pdoc['content'], CONTENT)
    self.assertEqual(pdoc['owner_uid'], UID)
    self.assertEqual(pdoc['doc_id'], pid)
    pdocs = await problem.get_list(DOMAIN_ID, fields=['doc_id', 'title'])
    self.assertEqual(len(pdocs), 1)
    self.assertEqual(pdocs[0]['doc_id'], pid)
    self.assertEqual(pdocs[0]['title'], TITLE)
    self.assertFalse('content' in pdocs[0])

  @base.wrap_coro
  async def test_star(self):
    await problem.add(DOMAIN_ID, TITLE, CONTENT, UID, PID)
    pdocs = await problem.get_list(DOMAIN_ID, uid=UID)
    self.assertFalse(pdocs[0]['psdoc'].get('star'))
    await problem.set_star(DOMAIN_ID, PID, UID, True)
    pdocs = await problem.get_list(DOMAIN_ID, uid=UID)
    self.assertTrue(pdocs[0]['psdoc'].get('star'))
    pdocs = await problem.get_list(DOMAIN_ID, uid=UID2)
    self.assertFalse(pdocs[0]['psdoc'].get('star'))
    await problem.set_star(DOMAIN_ID, PID, UID2, False)
    pdocs = await problem.get_list(DOMAIN_ID, uid=UID)
    self.assertTrue(pdocs[0]['psdoc'].get('star'))


class ProblemSolutionTest(base.DatabaseTestCase):
  def setUp(self):
    super(ProblemSolutionTest, self).setUp()
    base.wait(problem.add(DOMAIN_ID, TITLE, CONTENT, UID, PID))

  @base.wrap_coro
  async def test_initial_empty(self):
    psdocs = await problem.get_list_solution(DOMAIN_ID, PID)
    self.assertEqual(psdocs, [])

  @base.wrap_coro
  async def test_add_get(self):
    psid = await problem.add_solution(DOMAIN_ID, PID, UID2, CONTENT2)
    psdoc = await problem.get_solution(DOMAIN_ID, psid)
    self.assertEqual(psdoc['domain_id'], DOMAIN_ID)
    self.assertEqual(psdoc['content'], CONTENT2)
    self.assertEqual(psdoc['owner_uid'], UID2)
    self.assertEqual(psdoc['doc_id'], psid)
    psdocs = await problem.get_list_solution(DOMAIN_ID, PID, fields=['owner_uid', 'content'])
    self.assertEqual(len(psdocs), 1)
    self.assertEqual(psdocs[0]['owner_uid'], UID2)
    self.assertEqual(psdocs[0]['content'], CONTENT2)
    self.assertFalse('doc_id' in psdocs[0])

  @base.wrap_coro
  async def test_vote(self):
    psid = await problem.add_solution(DOMAIN_ID, PID, UID2, CONTENT2)
    psdoc = await problem.get_solution(DOMAIN_ID, psid)
    self.assertEqual(psdoc['vote'], 0)
    psdoc = await problem.vote_solution(DOMAIN_ID, psid, UID, 1)
    self.assertEqual(psdoc['vote'], 1)
    psdoc = await problem.vote_solution(DOMAIN_ID, psid, UID2, 1)
    self.assertEqual(psdoc['vote'], 2)
    with self.assertRaises(error.AlreadyVotedError):
      psdoc = await problem.vote_solution(DOMAIN_ID, psid, UID2, 1)
    psdoc = await problem.vote_solution(DOMAIN_ID, psid, UID2, -1)
    self.assertEqual(psdoc['vote'], 1)

  @base.wrap_coro
  async def test_reply(self):
    psid = await problem.add_solution(DOMAIN_ID, PID, UID2, CONTENT2)
    psdoc = await problem.get_solution(DOMAIN_ID, psid)
    self.assertEqual(psdoc['reply'], [])
    psdoc = await problem.reply_solution(DOMAIN_ID, psid, UID, CONTENT)
    self.assertEqual(len(psdoc['reply']), 1)
    self.assertEqual(psdoc['reply'][0]['content'], CONTENT)
    self.assertEqual(psdoc['reply'][0]['owner_uid'], UID)


if __name__ == '__main__':
  unittest.main()
