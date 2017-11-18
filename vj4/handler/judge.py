import asyncio
import calendar
import datetime
import logging
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import job
from vj4.handler import base
from vj4.model import builtin
from vj4.model import domain
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.model.adaptor import setting
from vj4.service import bus
from vj4.service import queue
from vj4.util import locale

_logger = logging.getLogger(__name__)


async def _send_ac_mail(handler, rdoc):
  udoc = await user.get_by_uid(rdoc['uid'])
  if not udoc:
    return
  u = setting.UserSetting(udoc)
  if not u.get_setting('send_code'):
    return
  if rdoc.get('hidden') and not handler.udoc_has_priv(udoc, builtin.PRIV_VIEW_HIDDEN_RECORD):
    return
  translate = locale.get_translate(u.get_setting('view_lang'))
  pdoc = await problem.get(rdoc['domain_id'], rdoc['pid'])
  await handler.send_mail(udoc['mail'],
                          translate('P{0} - {1} Accepted!').format(pdoc['doc_id'], pdoc['title']),
                          'ac_mail.html', rdoc=rdoc, pdoc=pdoc, _=translate)


async def _post_judge(handler, rdoc):
  accept = rdoc['status'] == constant.record.STATUS_ACCEPTED
  bus.publish_throttle('record_change', rdoc, rdoc['_id'])
  post_coros = list()
  # TODO(twd2): ignore no effect statuses like system error, ...
  if rdoc['type'] == constant.record.TYPE_SUBMISSION:
    if accept:
      post_coros.append(_send_ac_mail(handler, rdoc))
    if rdoc['tid']:
      post_coros.append(contest.update_status(rdoc['domain_id'], rdoc['tid'], rdoc['uid'],
                                              rdoc['_id'], rdoc['pid'], accept, rdoc['score']))
    if not rdoc.get('rejudged'):
      if await problem.update_status(rdoc['domain_id'], rdoc['pid'], rdoc['uid'],
                                     rdoc['_id'], rdoc['status']):
        if accept:
          # TODO(twd2): enqueue rdoc['pid'] to recalculate rp.
          await problem.inc(rdoc['domain_id'], rdoc['pid'], 'num_accept', 1)
          post_coros.append(domain.inc_user(rdoc['domain_id'], rdoc['uid'], num_accept=1))
    else:
      # TODO(twd2): enqueue rdoc['pid'] to recalculate rp.
      await job.record.user_in_problem(rdoc['uid'], rdoc['domain_id'], rdoc['pid'])
    post_coros.append(job.difficulty.update_problem(rdoc['domain_id'], rdoc['pid']))
  await asyncio.gather(*post_coros)


@app.route('/judge/playground', 'judge_playground')
class JudgePlaygroundHandler(base.Handler):
  @base.require_priv(builtin.PRIV_READ_RECORD_CODE | builtin.PRIV_WRITE_RECORD
                     | builtin.PRIV_READ_PROBLEM_DATA | builtin.PRIV_READ_PRETEST_DATA)
  async def get(self):
    self.render('judge_playground.html')


@app.route('/judge/noop', 'judge_noop')
class JudgeNoopHandler(base.Handler):
  @base.require_priv(builtin.JUDGE_PRIV)
  async def get(self):
    self.json({})


@app.route('/judge/datalist', 'judge_datalist')
class JudgeDataListHandler(base.Handler):
  @base.get_argument
  @base.sanitize
  async def get(self, last: int=0):
    # TODO(iceboy): This function looks strange.
    # Judge will have PRIV_READ_PROBLEM_DATA,
    # domain administrator will have PERM_READ_PROBLEM_DATA.
    if not self.has_priv(builtin.PRIV_READ_PROBLEM_DATA):
      self.check_perm(builtin.PERM_READ_PROBLEM_DATA)
    pids = await problem.get_data_list(last)
    datalist = []
    for domain_id, pid in pids:
      datalist.append({'domain_id': domain_id, 'pid': pid})
    self.json({'pids': datalist,
               'time': calendar.timegm(datetime.datetime.utcnow().utctimetuple())})


# TODO(iceboy): Move this to RecordCancelHandler.
@app.route('/judge/{rid}/score', 'judge_score')
class JudgeScoreHandler(base.Handler):
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, rid: objectid.ObjectId, score: int, message: str=''):
    rdoc = await record.get(rid)
    if rdoc['domain_id'] == self.domain_id:
      self.check_perm(builtin.PERM_REJUDGE)
    else:
      self.check_priv(builtin.PRIV_REJUDGE)
    await record.rejudge(rdoc['_id'], False)
    await record.begin_judge(rid, self.user['_id'], self.user['_id'],
                             constant.record.STATUS_FETCHED)
    update = {'$set': {}, '$push': {}}
    update['$set']['status'] = constant.record.STATUS_ACCEPTED if score == 100 \
                               else constant.record.STATUS_WRONG_ANSWER
    update['$push']['cases'] = {
      'status': update['$set']['status'],
      'score': score,
      'time_ms': 0,
      'memory_kb': 0,
      'judge_text': message,
    }
    await record.next_judge(rid, self.user['_id'], self.user['_id'], **update)
    rdoc = await record.end_judge(rid, self.user['_id'], self.user['_id'],
                                  update['$set']['status'], score, 0, 0)
    await _post_judge(self, rdoc)
    self.json_or_redirect(self.referer_or_main)


@app.connection_route('/judge/consume-conn', 'judge_consume-conn')
class JudgeNotifyConnection(base.Connection):
  @base.require_priv(builtin.PRIV_READ_RECORD_CODE | builtin.PRIV_WRITE_RECORD)
  async def on_open(self):
    self.rids = {}  # delivery_tag -> rid
    bus.subscribe(self.on_problem_data_change, ['problem_data_change'])
    self.channel = await queue.consume('judge', self._on_queue_message)
    asyncio.ensure_future(self.channel.close_event.wait()).add_done_callback(lambda _: self.close())

  async def on_problem_data_change(self, e):
    domain_id_pid = dict(e['value'])
    self.send(event=e['key'], **domain_id_pid)

  async def _on_queue_message(self, tag, *, rid):
    rdoc = await record.begin_judge(rid, self.user['_id'], self.id,
                                    constant.record.STATUS_FETCHED)
    if rdoc:
      self.rids[tag] = rdoc['_id']
      self.send(rid=str(rdoc['_id']), tag=tag, pid=str(rdoc['pid']), domain_id=rdoc['domain_id'],
                lang=rdoc['lang'], code=rdoc['code'], type=rdoc['type'])
      bus.publish_throttle('record_change', rdoc, rdoc['_id'])
    else:
      # Record not found, eat it.
      await self.channel.basic_client_ack(tag)

  async def on_message(self, *, key, tag, **kwargs):
    if key == 'next':
      rid = self.rids[tag]
      update = {}
      if 'status' in kwargs:
        update.setdefault('$set', {})['status'] = int(kwargs['status'])
      if 'compiler_text' in kwargs:
        update.setdefault('$push', {})['compiler_texts'] = str(kwargs['compiler_text'])
      if 'judge_text' in kwargs:
        update.setdefault('$push', {})['judge_texts'] = str(kwargs['judge_text'])
      if 'case' in kwargs:
        update.setdefault('$push', {})['cases'] = {
          'status': int(kwargs['case']['status']),
          'score': int(kwargs['case']['score']),
          'time_ms': int(kwargs['case']['time_ms']),
          'memory_kb': int(kwargs['case']['memory_kb']),
          'judge_text': str(kwargs['case']['judge_text']),
        }
      if 'progress' in kwargs:
        update.setdefault('$set', {})['progress'] = float(kwargs['progress'])
      rdoc = await record.next_judge(rid, self.user['_id'], self.id, **update)
      if not rdoc:
        return
      bus.publish_throttle('record_change', rdoc, rdoc['_id'])
    elif key == 'end':
      rid = self.rids.pop(tag)
      rdoc, _ = await asyncio.gather(record.end_judge(rid, self.user['_id'], self.id,
                                                      int(kwargs['status']),
                                                      int(kwargs['score']),
                                                      int(kwargs['time_ms']),
                                                      int(kwargs['memory_kb'])),
                                     self.channel.basic_client_ack(tag))
      if not rdoc:
        return
      await _post_judge(self, rdoc)

  async def on_close(self):
    async def close():
      async def reset_record(rid):
        rdoc = await record.end_judge(rid, self.user['_id'], self.id,
                                      constant.record.STATUS_WAITING, 0, 0, 0)
        bus.publish_throttle('record_change', rdoc, rdoc['_id'])

      await asyncio.gather(*[reset_record(rid) for rid in self.rids.values()])
      await self.channel.close()

    asyncio.get_event_loop().create_task(close())
