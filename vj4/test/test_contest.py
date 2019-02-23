import datetime
import functools
import unittest

from bson import objectid

from vj4 import constant
from vj4 import error
from vj4.model import document
from vj4.model.adaptor import contest
from vj4.test import base


def _rule_test_stat(tdoc, journal):
  def time(jdoc):
    delta_time = jdoc['rid'].generation_time.replace(tzinfo=None) - tdoc['begin_at']
    return delta_time.total_seconds()

  detail = [{**j, 'time': time(j)} for j in journal]
  return {'score': sum(d['score'] for d in detail),
          'time': sum(d['time'] for d in detail),
          'detail': detail}


NOW = datetime.datetime.utcnow().replace(microsecond=0)
TDOC = {'pids': [777, 778, 779], 'begin_at': NOW}
ASSDOC = {'pids': [777, 778, 779], 'begin_at': NOW,
          'penalty_since': NOW + datetime.timedelta(seconds=5),
          'penalty_rules': {'1': 0.9, '2': 0.8, '3': 0.6, '4': 0.2}}
SUBMIT_777_AC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=2)),
                 'pid': 777, 'accept': True, 'score': 22}
SUBMIT_777_AC_LATE = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=7)),
                      'pid': 777, 'accept': True, 'score': 17}
SUBMIT_777_NAC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=3)),
                  'pid': 777, 'accept': False, 'score': 44}
SUBMIT_777_NAC_LATE = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=12)),
                       'pid': 777, 'accept': False, 'score': 23}
SUBMIT_778_AC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=4)),
                 'pid': 778, 'accept': True, 'score': 33}
SUBMIT_778_AC_LATE = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=8)),
                      'pid': 778, 'accept': True, 'score': 37}
SUBMIT_780_AC = {'rid': objectid.ObjectId.from_datetime(NOW + datetime.timedelta(seconds=5)),
                 'pid': 780, 'accept': True, 'score': 1000}

DOMAIN_ID_DUMMY = 'dummy'
OWNER_UID = 22
TITLE = 'dummy_title'
CONTENT = 'dummy_content'
ATTEND_UID = 44
RULE_TEST_ID = 999
RULE_TEST = contest.Rule(lambda tdoc, now: now > tdoc['begin_at'],
                         lambda tdoc, now: now > tdoc['begin_at'],
                         _rule_test_stat,
                         [('score', -1), ('time', -1)],
                         functools.partial(enumerate, start=1),
                         lambda **kwargs: None)


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


class AssignmentRuleTest(unittest.TestCase):
  def test_zero(self):
    stats = contest._assignment_stat(ASSDOC, [])
    self.assertEqual(stats['score'], 0)
    self.assertEqual(stats['penalty_score'], 0)
    self.assertEqual(stats['time'], 0)
    self.assertEqual(stats['detail'], [])

  def test_one_ac(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_AC])
    self.assertEqual(stats['score'], 22)
    self.assertEqual(stats['penalty_score'], 22)
    self.assertEqual(stats['time'], 2)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'penalty_score': 22, 'time': 2}])

  def test_one_late_ac(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_AC_LATE])
    self.assertEqual(stats['score'], 17)
    self.assertEqual(stats['penalty_score'], 17 * 0.8)
    self.assertEqual(stats['time'], 7)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC_LATE, 'penalty_score': 17 * 0.8, 'time': 7}])

  def test_one_late_nac(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_NAC_LATE])
    self.assertEqual(stats['score'], 23)
    self.assertEqual(stats['penalty_score'], 23 * 0.2)
    self.assertEqual(stats['time'], 12)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_NAC_LATE, 'penalty_score': 23 * 0.2, 'time': 12}])

  def test_one_nac_late_ac_late(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_NAC_LATE, SUBMIT_777_AC_LATE])
    self.assertEqual(stats['score'], 17)
    self.assertEqual(stats['penalty_score'], 17 * 0.8)
    self.assertEqual(stats['time'], 7)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC_LATE, 'penalty_score': 17 * 0.8, 'time': 7}])

  def test_one_ac_late_nac_late(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_AC_LATE, SUBMIT_777_NAC_LATE])
    self.assertEqual(stats['score'], 17)
    self.assertEqual(stats['penalty_score'], 17 * 0.8)
    self.assertEqual(stats['time'], 7)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC_LATE, 'penalty_score': 17 * 0.8, 'time': 7}])

  def test_one_ac_nac(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_AC, SUBMIT_777_NAC])
    self.assertEqual(stats['score'], 22)
    self.assertEqual(stats['penalty_score'], 22)
    self.assertEqual(stats['time'], 2)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'penalty_score': 22, 'time': 2}])

  def test_one_ac_nac_late(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_AC, SUBMIT_777_NAC_LATE])
    self.assertEqual(stats['score'], 22)
    self.assertEqual(stats['penalty_score'], 22)
    self.assertEqual(stats['time'], 2)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_AC, 'penalty_score': 22, 'time': 2}])

  def test_one_nac_nac_late(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_777_NAC, SUBMIT_777_NAC_LATE])
    self.assertEqual(stats['score'], 23)
    self.assertEqual(stats['penalty_score'], 23 * 0.2)
    self.assertEqual(stats['time'], 12)
    self.assertEqual(stats['detail'], [{**SUBMIT_777_NAC_LATE, 'penalty_score': 23 * 0.2, 'time': 12}])

  def test_multiple_1(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_778_AC, SUBMIT_777_NAC])
    self.assertEqual(stats['score'], 33 + 44)
    self.assertEqual(stats['penalty_score'], 33 + 44)
    self.assertEqual(stats['time'], 4 + 3)
    self.assertCountEqual(stats['detail'],
                          [{**SUBMIT_778_AC, 'penalty_score': 33, 'time': 4},
                           {**SUBMIT_777_NAC, 'penalty_score': 44, 'time': 3}])

  def test_multiple_2(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_778_AC, SUBMIT_777_NAC_LATE])
    self.assertEqual(stats['score'], 33 + 23)
    self.assertEqual(stats['penalty_score'], 33 + 23 * 0.2)
    self.assertEqual(stats['time'], 4 + 12)
    self.assertCountEqual(stats['detail'],
                          [{**SUBMIT_778_AC, 'penalty_score': 33, 'time': 4},
                           {**SUBMIT_777_NAC_LATE, 'penalty_score': 23 * 0.2, 'time': 12}])

  def test_multiple_3(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_778_AC, SUBMIT_777_NAC, SUBMIT_778_AC_LATE, SUBMIT_777_AC_LATE])
    self.assertEqual(stats['score'], 33 + 17)
    self.assertEqual(stats['penalty_score'], 33 + 17 * 0.8)
    self.assertEqual(stats['time'], 4 + 7)
    self.assertCountEqual(stats['detail'],
                          [{**SUBMIT_778_AC, 'penalty_score': 33, 'time': 4},
                           {**SUBMIT_777_AC_LATE, 'penalty_score': 17 * 0.8, 'time': 7}])

  def test_inject(self):
    stats = contest._assignment_stat(ASSDOC, [SUBMIT_780_AC])
    self.assertEqual(stats['score'], 0)
    self.assertEqual(stats['penalty_score'], 0)
    self.assertEqual(stats['time'], 0)
    self.assertEqual(stats['detail'], [])


class OuterTest(base.DatabaseTestCase):
  @base.wrap_coro
  async def test_add_get(self):
    begin_at = datetime.datetime.utcnow()
    end_at = begin_at + datetime.timedelta(seconds=22)
    tid = await contest.add(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, TITLE, CONTENT, OWNER_UID,
                            constant.contest.RULE_ACM, begin_at, end_at)
    tdoc = await contest.get(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, tid)
    self.assertEqual(tdoc['doc_id'], tid)
    self.assertEqual(tdoc['domain_id'], DOMAIN_ID_DUMMY)
    self.assertEqual(tdoc['owner_uid'], OWNER_UID)
    self.assertEqual(tdoc['title'], TITLE)
    self.assertEqual(tdoc['content'], CONTENT)
    tdocs = await contest.get_multi(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, fields=['title']).to_list()
    self.assertEqual(len(tdocs), 1)
    self.assertEqual(tdocs[0]['title'], TITLE)
    self.assertFalse('content' in tdocs[0])


class InnerTest(base.DatabaseTestCase):
  def setUp(self):
    super(InnerTest, self).setUp()
    begin_at = NOW
    end_at = NOW + datetime.timedelta(seconds=22)
    constant.contest.CONTEST_RULES.append(RULE_TEST_ID)
    contest.RULES[RULE_TEST_ID] = RULE_TEST
    self.tid = base.wait(contest.add(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, TITLE, CONTENT, OWNER_UID,
                                     RULE_TEST_ID, begin_at, end_at, [777, 778, 780]))

  def tearDown(self):
    super(InnerTest, self).tearDown()
    constant.contest.CONTEST_RULES.remove(RULE_TEST_ID)
    del contest.RULES[RULE_TEST_ID]

  @base.wrap_coro
  async def test_attend(self):
    tdoc = await contest.get(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    self.assertEqual(tdoc['attend'], 0)
    _, tsdocs = await contest.get_and_list_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    self.assertEqual(len(tsdocs), 0)
    tdoc = await contest.attend(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    self.assertEqual(tdoc['attend'], 1)
    _, tsdocs = await contest.get_and_list_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    self.assertEqual(len(tsdocs), 1)
    self.assertEqual(tsdocs[0]['uid'], ATTEND_UID)

  @base.wrap_coro
  async def test_attend_twice(self):
    await contest.attend(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    with self.assertRaises(error.ContestAlreadyAttendedError):
      await contest.attend(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)

  @base.wrap_coro
  async def test_update_status_none(self):
    rid = objectid.ObjectId()
    with self.assertRaises(error.ContestNotAttendedError):
      await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_777_AC)

  @base.wrap_coro
  async def test_update_status(self):
    await contest.attend(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_777_AC)
    await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_777_NAC)
    await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_778_AC)
    tsdoc = await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_780_AC)
    self.assertEqual(len(tsdoc['journal']), 4)
    self.assertEqual(tsdoc['journal'][0], SUBMIT_777_AC)
    self.assertEqual(tsdoc['journal'][1], SUBMIT_777_NAC)
    self.assertEqual(tsdoc['journal'][2], SUBMIT_778_AC)
    self.assertEqual(tsdoc['journal'][3], SUBMIT_780_AC)
    self.assertEqual(tsdoc['score'], 1099)
    self.assertEqual(tsdoc['time'], 14)
    self.assertEqual(len(tsdoc['detail']), 4)
    self.assertEqual(tsdoc['detail'][0]['time'], 2)
    self.assertEqual(tsdoc['detail'][1]['time'], 3)
    self.assertEqual(tsdoc['detail'][2]['time'], 4)
    self.assertEqual(tsdoc['detail'][3]['time'], 5)

  @base.wrap_coro
  async def test_recalc_status(self):
    await contest.attend(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_777_AC)
    await contest.edit(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, begin_at=NOW - datetime.timedelta(seconds=3))
    await contest.recalc_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    tsdoc = await contest.get_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    self.assertEqual(len(tsdoc['journal']), 1)
    self.assertEqual(tsdoc['journal'][0], SUBMIT_777_AC)
    self.assertEqual(tsdoc['score'], 22)
    self.assertEqual(tsdoc['time'], 5)
    self.assertEqual(len(tsdoc['detail']), 1)
    self.assertEqual(tsdoc['detail'][0]['time'], 5)
    await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_777_NAC)
    await contest.edit(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, begin_at=NOW - datetime.timedelta(seconds=5))
    await contest.recalc_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    tsdoc = await contest.get_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    self.assertEqual(len(tsdoc['journal']), 2)
    self.assertEqual(tsdoc['journal'][0], SUBMIT_777_AC)
    self.assertEqual(tsdoc['journal'][1], SUBMIT_777_NAC)
    self.assertEqual(tsdoc['score'], 66)
    self.assertEqual(tsdoc['time'], 15)
    self.assertEqual(len(tsdoc['detail']), 2)
    self.assertEqual(tsdoc['detail'][0]['time'], 7)
    self.assertEqual(tsdoc['detail'][1]['time'], 8)
    await contest.update_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID, **SUBMIT_778_AC)
    await contest.edit(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, begin_at=NOW - datetime.timedelta(seconds=3))
    await contest.recalc_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    tsdoc = await contest.get_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    self.assertEqual(len(tsdoc['journal']), 3)
    self.assertEqual(tsdoc['journal'][0], SUBMIT_777_AC)
    self.assertEqual(tsdoc['journal'][1], SUBMIT_777_NAC)
    self.assertEqual(tsdoc['journal'][2], SUBMIT_778_AC)
    self.assertEqual(tsdoc['score'], 99)
    self.assertEqual(tsdoc['time'], 18)
    self.assertEqual(len(tsdoc['detail']), 3)
    self.assertEqual(tsdoc['detail'][0]['time'], 5)
    self.assertEqual(tsdoc['detail'][1]['time'], 6)
    self.assertEqual(tsdoc['detail'][2]['time'], 7)
    tsdoc_old = tsdoc
    await contest.recalc_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid)
    tsdoc = await contest.get_status(DOMAIN_ID_DUMMY, document.TYPE_CONTEST, self.tid, ATTEND_UID)
    self.assertEqual(tsdoc['rev'], tsdoc_old['rev'] + 1)
    del tsdoc['rev']
    del tsdoc_old['rev']
    self.assertEqual(tsdoc, tsdoc_old)

if __name__ == '__main__':
  unittest.main()
