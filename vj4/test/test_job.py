import unittest

from vj4 import constant
from vj4 import job
from vj4.model import domain
from vj4.model import record
from vj4.model.adaptor import problem
from vj4.test import base

DOMAIN_ID = 'system'
OWNER_UID = 20
UID = 22
UNAME = 'twd2'
UID2 = 23
UNAME2 = 'twd3'
JUDGE_UID = 0
JUDGE_TOKEN = 'token'

EPS = 10 ** (-5)


class RecordTestCase(base.DatabaseTestCase):
  async def init_record(self):
    self.pid1 = await problem.add(DOMAIN_ID, 'a+b', 'calc a+b', OWNER_UID)
    self.pid2 = await problem.add(DOMAIN_ID, 'a-b', 'calc a-b', OWNER_UID)
    self.rid_p1_wa_to_ac = await record.add(DOMAIN_ID, self.pid1, constant.record.TYPE_SUBMISSION,
                                            UID, 'cc', 'int main(){}')
    self.rid_p1_ac = await record.add(DOMAIN_ID, self.pid1, constant.record.TYPE_SUBMISSION,
                                      UID, 'cc', 'int main(){}')
    self.rid_p1_ac2 = await record.add(DOMAIN_ID, self.pid1, constant.record.TYPE_SUBMISSION,
                                       UID, 'cc', 'int main(){}')
    # first judge, WA. rejudge, TODO(twd2)
    await record.begin_judge(self.rid_p1_wa_to_ac, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p1_wa_to_ac, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 50, 1000, 1024)
    await record.begin_judge(self.rid_p1_ac, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p1_ac, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_ACCEPTED, 100, 1000, 1024)
    await record.begin_judge(self.rid_p1_ac2, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p1_ac2, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_ACCEPTED, 100, 1000, 1024)
    self.rid_p2_wa = await record.add(DOMAIN_ID, self.pid2, constant.record.TYPE_SUBMISSION,
                                      UID, 'cc', 'int main(){}')
    self.rid_p2_wa2 = await record.add(DOMAIN_ID, self.pid2, constant.record.TYPE_SUBMISSION,
                                       UID, 'cc', 'int main(){}')
    self.rid_p2_ac = await record.add(DOMAIN_ID, self.pid2, constant.record.TYPE_SUBMISSION,
                                      UID, 'cc', 'int main(){}')
    self.rid_p2_wa3 = await record.add(DOMAIN_ID, self.pid2, constant.record.TYPE_SUBMISSION,
                                       UID, 'cc', 'int main(){}')
    await record.begin_judge(self.rid_p2_wa, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p2_wa, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 60, 1000, 1024)
    await record.begin_judge(self.rid_p2_wa2, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p2_wa2, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 70, 1000, 1024)
    await record.begin_judge(self.rid_p2_ac, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p2_ac, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_ACCEPTED, 100, 1000, 1024)
    await record.begin_judge(self.rid_p2_wa3, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p2_wa3, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 80, 1000, 1024)
    self.rid_p1u2_wa = await record.add(DOMAIN_ID, self.pid1, constant.record.TYPE_SUBMISSION,
                                        UID2, 'cc', 'int main(){}')
    await record.begin_judge(self.rid_p1u2_wa, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p1u2_wa, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 0, 1000, 1024)
    self.rid_p2u2_wa = await record.add(DOMAIN_ID, self.pid2, constant.record.TYPE_SUBMISSION,
                                        UID2, 'cc', 'int main(){}')
    await record.begin_judge(self.rid_p2u2_wa, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p2u2_wa, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 10, 1000, 1024)    


class RecordTest(RecordTestCase):
  @base.wrap_coro
  async def test_run(self):
    await self.init_record()
    await job.record.run(DOMAIN_ID)
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID)
    self.assertEqual(pdoc['num_submit'], 4)
    self.assertEqual(pdoc['num_accept'], 1)
    psdoc = pdoc['psdoc']
    self.assertEqual(psdoc['num_submit'], 3)
    self.assertEqual(psdoc['status'], constant.record.STATUS_ACCEPTED)
    self.assertEqual(psdoc['rid'], self.rid_p1_ac)
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID2)
    self.assertEqual(pdoc['num_submit'], 4)
    self.assertEqual(pdoc['num_accept'], 1)
    psdoc = pdoc['psdoc']
    self.assertEqual(psdoc['num_submit'], 1)
    self.assertEqual(psdoc['status'], constant.record.STATUS_WRONG_ANSWER)
    self.assertEqual(psdoc['rid'], self.rid_p1u2_wa)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID)
    self.assertEqual(pdoc['num_submit'], 5)
    self.assertEqual(pdoc['num_accept'], 1)
    psdoc = pdoc['psdoc']
    self.assertEqual(psdoc['num_submit'], 4)
    self.assertEqual(psdoc['status'], constant.record.STATUS_ACCEPTED)
    self.assertEqual(psdoc['rid'], self.rid_p2_ac)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID2)
    self.assertEqual(pdoc['num_submit'], 5)
    self.assertEqual(pdoc['num_accept'], 1)
    psdoc = pdoc['psdoc']
    self.assertEqual(psdoc['num_submit'], 1)
    self.assertEqual(psdoc['status'], constant.record.STATUS_WRONG_ANSWER)
    self.assertEqual(psdoc['rid'], self.rid_p2u2_wa)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['num_submit'], 7)
    self.assertEqual(dudoc['num_accept'], 2)
    dudoc = await domain.get_user(DOMAIN_ID, UID2)
    self.assertEqual(dudoc['num_submit'], 2)
    self.assertEqual(dudoc['num_accept'], 0)


class RpTest(RecordTestCase):
  @base.wrap_coro
  async def test_recalc(self):
    await self.init_record()
    await job.record.run(DOMAIN_ID)
    await job.rp.recalc(DOMAIN_ID)
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID)
    psdoc = pdoc['psdoc']
    rp_p1 = psdoc['rp']
    self.assertGreater(rp_p1, 0)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID)
    psdoc = pdoc['psdoc']
    rp_p2 = psdoc['rp']
    self.assertGreater(rp_p2, 0)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['rp'], rp_p1 + rp_p2)
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID2)
    psdoc = pdoc['psdoc']
    self.assertTrue('rp' not in psdoc or psdoc['rp'] == 0)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID2)
    psdoc = pdoc['psdoc']
    self.assertTrue('rp' not in psdoc or psdoc['rp'] == 0)
    dudoc = await domain.get_user(DOMAIN_ID, UID2)
    self.assertTrue('rp' not in dudoc or dudoc['rp'] == 0)

  @base.wrap_coro
  async def test_update_problem(self):
    await self.init_record()
    await job.record.run(DOMAIN_ID)
    await job.rp.recalc(DOMAIN_ID)
    # user 1
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID)
    psdoc = pdoc['psdoc']
    rp_p1_before = psdoc['rp']
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID)
    psdoc = pdoc['psdoc']
    rp_p2_before = psdoc['rp']
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    rp_u1_before = dudoc['rp']
    # user 1 submitted a record, WA
    rid_p1_wa2 = await record.add(DOMAIN_ID, self.pid1, constant.record.TYPE_SUBMISSION,
                                  UID, 'cc', 'int main(){}')
    await record.begin_judge(rid_p1_wa2, JUDGE_UID, JUDGE_TOKEN, constant.record.STATUS_JUDGING)
    await record.end_judge(rid_p1_wa2, JUDGE_UID, JUDGE_TOKEN, constant.record.STATUS_WRONG_ANSWER,
                           50, 1000, 1024)
    # user 2 submitted a record, AC
    rid_p1u2_ac = await record.add(DOMAIN_ID, self.pid1, constant.record.TYPE_SUBMISSION,
                                   UID2, 'cc', 'int main(){}')
    await record.begin_judge(rid_p1u2_ac, JUDGE_UID, JUDGE_TOKEN, constant.record.STATUS_JUDGING)
    await record.end_judge(rid_p1u2_ac, JUDGE_UID, JUDGE_TOKEN, constant.record.STATUS_ACCEPTED,
                           100, 1000, 1024)
    await job.record.run(DOMAIN_ID)
    await job.rp.update_problem(DOMAIN_ID, self.pid1)
    await job.rp.update_problem(DOMAIN_ID, self.pid2)
    # user 1
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID)
    psdoc = pdoc['psdoc']
    rp_p1 = psdoc['rp']
    self.assertGreater(rp_p1, 0)
    self.assertLess(rp_p1, rp_p1_before)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID)
    psdoc = pdoc['psdoc']
    rp_p2 = psdoc['rp']
    self.assertGreater(rp_p2, 0)
    self.assertEqual(rp_p2, rp_p2_before)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertEqual(dudoc['rp'], rp_p1 + rp_p2)
    self.assertLess(dudoc['rp'], rp_u1_before)
    # user 2
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID2)
    psdoc = pdoc['psdoc']
    rp_p1u2 = psdoc['rp']
    self.assertGreater(rp_p1u2, 0)
    self.assertLess(rp_p1u2, rp_p1)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID2)
    psdoc = pdoc['psdoc']
    self.assertTrue('rp' not in psdoc or psdoc['rp'] == 0)
    dudoc = await domain.get_user(DOMAIN_ID, UID2)
    self.assertEqual(dudoc['rp'], rp_p1u2)
    # rejudge to WA
    await record.begin_judge(self.rid_p2_ac, JUDGE_UID, JUDGE_TOKEN,
                             constant.record.STATUS_JUDGING)
    await record.end_judge(self.rid_p2_ac, JUDGE_UID, JUDGE_TOKEN,
                           constant.record.STATUS_WRONG_ANSWER, 10, 1000, 1024)
    await job.record.run(DOMAIN_ID)
    await job.rp.update_problem(DOMAIN_ID, self.pid1)
    await job.rp.update_problem(DOMAIN_ID, self.pid2)
    # user 1
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID)
    psdoc = pdoc['psdoc']
    rp_p1_after = psdoc['rp']
    self.assertEqual(rp_p1, rp_p1_after)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID)
    psdoc = pdoc['psdoc']
    self.assertTrue('rp' not in psdoc or psdoc['rp'] == 0)
    dudoc = await domain.get_user(DOMAIN_ID, UID)
    self.assertTrue(abs(dudoc['rp'] - rp_p1_after) < EPS)
    # user 2
    pdoc = await problem.get(DOMAIN_ID, self.pid1, UID2)
    psdoc = pdoc['psdoc']
    rp_p1u2_after = psdoc['rp']
    self.assertEqual(rp_p1u2, rp_p1u2_after)
    pdoc = await problem.get(DOMAIN_ID, self.pid2, UID2)
    psdoc = pdoc['psdoc']
    self.assertTrue('rp' not in psdoc or psdoc['rp'] == 0)
    dudoc = await domain.get_user(DOMAIN_ID, UID2)
    self.assertEqual(dudoc['rp'], rp_p1u2_after)


class RankTest(RecordTestCase):
  @base.wrap_coro
  async def test_run(self):
    await self.init_record()
    await job.record.run(DOMAIN_ID)
    await job.rp.recalc(DOMAIN_ID)
    await job.rank.run(DOMAIN_ID)
    dudoc1 = await domain.get_user(DOMAIN_ID, UID)
    dudoc2 = await domain.get_user(DOMAIN_ID, UID2)
    self.assertEqual(dudoc1['rank'], 1)
    self.assertEqual(dudoc2['rank'], 2)
    self.assertGreaterEqual(dudoc1['level'], dudoc2['level'])


class DifficultyTest(unittest.TestCase):
  def test_integrate(self):
    for x in range(1000):
      self.assertEqual(job.difficulty._integrate(x), job.difficulty._integrate_direct(x))
