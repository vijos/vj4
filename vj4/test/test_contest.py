import datetime
import unittest

from bson import objectid

from vj4 import constant
from vj4 import error
from vj4.model.adaptor import contest
from vj4.test import base

NOW = datetime.datetime.utcnow().replace(microsecond=0)
TDOC = {'pids': [777, 778, 779], 'begin_at': NOW}
SUBMIT_777_AC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=2)),
                 'pid': 777, 'accept': True, 'score': 22}
SUBMIT_777_NAC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=3)),
                  'pid': 777, 'accept': False, 'score': 44}
SUBMIT_778_AC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=4)),
                 'pid': 778, 'accept': True, 'score': 33}
SUBMIT_780_AC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=5)),
                 'pid': 780, 'accept': True, 'score': 1000}

DOMAIN_ID_DUMMY = 'dummy'
OWNER_UID = 22
TITLE = 'dummy_title'
CONTENT = 'dummy_content'
ATTEND_UID = 44


class OiRuleTest(unittest.TestCase):
  def test_zero(self):
    stats = contest._oi_stat(TDOC, [])
    self.assertEqual(stats['score'], 0)
    self.assertEqual(stats['detail'], [])

  def test_one(self):
    stats = contest._oi_stat(TDOC, [SUBMIT_777_AC])
    self.assertEqual(stats['score'], SUBMIT_777_AC['score'])
    self.assertEqual(stats['detail'], [SUBMIT_777_AC])

  def test_two(self):
    stats = contest._oi_stat(TDOC, [SUBMIT_778_AC, SUBMIT_777_AC])
    self.assertEqual(stats['score'], SUBMIT_778_AC['score'] + SUBMIT_777_AC['score'])
    self.assertCountEqual(stats['detail'], [SUBMIT_778_AC, SUBMIT_777_AC])

  def test_override(self):
    stats = contest._oi_stat(TDOC, [SUBMIT_777_NAC, SUBMIT_777_AC])
    self.assertEqual(stats['score'], SUBMIT_777_AC['score'])
    self.assertEqual(stats['detail'], [SUBMIT_777_AC])

  def test_inject(self):
    stats = contest._oi_stat(TDOC, [SUBMIT_780_AC])
    self.assertEqual(stats['score'], 0)
    self.assertEqual(stats['detail'], [])


class AcmRuleTest(unittest.TestCase):
  def test_zero(self):
    stats = contest._acm_stat(TDOC, [])
    self.assertEqual(stats['accept'], 0)
    self.assertEqual(stats['time'], 0)
    self.assertEqual(stats['detail'], [])

  def test_one_ac(self):
    stats = contest._acm_stat(TDOC, [SUBMIT_777_AC])
    self.assertEqual(stats['accept'], 1)
    self.assertEqual(stats['time'], 2)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'naccept': 0, 'time': 2}])

  def test_one_nac(self):
    stats = contest._acm_stat(TDOC, [SUBMIT_777_NAC])
    self.assertEqual(stats['accept'], 0)
    self.assertEqual(stats['time'], 0)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_NAC, 'naccept': 1, 'time': 1203}])

  def test_one_nac_ac(self):
    stats = contest._acm_stat(TDOC, [SUBMIT_777_NAC, SUBMIT_777_AC])
    self.assertEqual(stats['accept'], 1)
    self.assertEqual(stats['time'], 1202)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'naccept': 1, 'time': 1202}])

  def test_one_ac_nac(self):
    stats = contest._acm_stat(TDOC, [SUBMIT_777_AC, SUBMIT_777_NAC])
    self.assertEqual(stats['accept'], 1)
    self.assertEqual(stats['time'], 2)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'naccept': 0, 'time': 2}])

  def test_two(self):
    stats = contest._acm_stat(TDOC, [SUBMIT_777_AC, SUBMIT_778_AC])
    self.assertEqual(stats['accept'], 2)
    self.assertEqual(stats['time'], 6)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'naccept': 0, 'time': 2},
                                       {**SUBMIT_778_AC, 'naccept': 0, 'time': 4}])

  def test_inject(self):
    stats = contest._acm_stat(TDOC, [SUBMIT_780_AC])
    self.assertEqual(stats['accept'], 0)
    self.assertEqual(stats['time'], 0)
    self.assertEqual(stats['detail'], [])


class OuterTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_add_get(self):
    begin_at = datetime.datetime.utcnow()
    end_at = begin_at + datetime.timedelta(seconds=22)
    tid = await contest.add(DOMAIN_ID_DUMMY, TITLE, CONTENT, OWNER_UID,
                            constant.contest.RULE_ACM, begin_at, end_at)
    tdoc = await contest.get(DOMAIN_ID_DUMMY, tid)
    self.assertEqual(tdoc['doc_id'], tid)
    self.assertEqual(tdoc['domain_id'], DOMAIN_ID_DUMMY)
    self.assertEqual(tdoc['owner_uid'], OWNER_UID)
    self.assertEqual(tdoc['title'], TITLE)
    self.assertEqual(tdoc['content'], CONTENT)
    tdocs = await contest.get_multi(DOMAIN_ID_DUMMY, fields=['title']).to_list()
    self.assertEqual(len(tdocs), 1)
    self.assertEqual(tdocs[0]['title'], TITLE)
    self.assertFalse('content' in tdocs[0])


class InnerTest(base.DatabaseTestCase):
  def setUp(self):
    super(InnerTest, self).setUp()
    begin_at = NOW
    end_at = NOW + datetime.timedelta(seconds=22)
    self.tid = base.wait(contest.add(DOMAIN_ID_DUMMY, TITLE, CONTENT, OWNER_UID,
                                     constant.contest.RULE_ACM, begin_at, end_at, [1000, 1001, 1002]))
    # TODO(twd2): test RULE_OI

  @base.wrap_coro
  async def test_attend(self):
    tdoc = await contest.get(DOMAIN_ID_DUMMY, self.tid)
    self.assertEqual(tdoc['attend'], 0)
    _, tsdocs = await contest.get_and_list_status(DOMAIN_ID_DUMMY, self.tid)
    self.assertEqual(len(tsdocs), 0)
    tdoc = await contest.attend(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID)
    self.assertEqual(tdoc['attend'], 1)
    _, tsdocs = await contest.get_and_list_status(DOMAIN_ID_DUMMY, self.tid)
    self.assertEqual(len(tsdocs), 1)
    self.assertEqual(tsdocs[0]['uid'], ATTEND_UID)

  @base.wrap_coro
  async def test_attend_twice(self):
    await contest.attend(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID)
    with self.assertRaises(error.ContestAlreadyAttendedError):
      await contest.attend(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID)

  @base.wrap_coro
  async def test_update_status_wrong_pid(self):
    rid = objectid.ObjectId()
    with self.assertRaises(error.ValidationError):
      await contest.update_status(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID, rid, 777, True, 100)

  @base.wrap_coro
  async def test_update_status_none(self):
    rid = objectid.ObjectId()
    with self.assertRaises(error.ContestNotAttendedError):
      await contest.update_status(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID, rid, 1000, True, 100)

  @base.wrap_coro
  async def test_update_status(self):
    await contest.attend(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID)
    rid1 = objectid.ObjectId()
    await contest.update_status(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID, rid1, 1000, True, 100)
    rid2 = objectid.ObjectId()
    await contest.update_status(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID, rid2, 1001, False, 77)
    rid3 = objectid.ObjectId()
    tsdoc = await contest.update_status(DOMAIN_ID_DUMMY, self.tid, ATTEND_UID, rid3, 1002, True, 100)
    self.assertEqual(len(tsdoc['journal']), 3)
    self.assertEqual(tsdoc['journal'][0]['rid'], rid1)
    self.assertEqual(tsdoc['journal'][0]['pid'], 1000)
    self.assertEqual(tsdoc['journal'][0]['accept'], True)
    self.assertEqual(tsdoc['journal'][0]['score'], 100)
    self.assertEqual(tsdoc['journal'][1]['rid'], rid2)
    self.assertEqual(tsdoc['journal'][1]['pid'], 1001)
    self.assertEqual(tsdoc['journal'][1]['accept'], False)
    self.assertEqual(tsdoc['journal'][1]['score'], 77)
    self.assertEqual(tsdoc['journal'][2]['rid'], rid3)
    self.assertEqual(tsdoc['journal'][2]['pid'], 1002)
    self.assertEqual(tsdoc['journal'][2]['accept'], True)
    self.assertEqual(tsdoc['journal'][2]['score'], 100)


if __name__ == '__main__':
  unittest.main()
