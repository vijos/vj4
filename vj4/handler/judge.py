import asyncio
import logging
import time

from vj4 import app
from vj4 import constant
from vj4.model import builtin
from vj4.model import queue
from vj4.model import record
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.model.adaptor import training
from vj4.service import bus
from vj4.handler import base

_logger = logging.getLogger(__name__)


@app.route('/judge/playground', 'judge_playground')
class JudgePlaygroundView(base.Handler):
  @base.require_priv(builtin.PRIV_READ_RECORD_CODE | builtin.PRIV_WRITE_RECORD)
  async def get(self):
    self.render('judge_playground.html')


@app.route('/judge/noop', 'judge_noop')
class JudgeNoopView(base.Handler):
  @base.require_priv(builtin.PRIV_READ_RECORD_CODE | builtin.PRIV_WRITE_RECORD)
  async def get(self):
    self.json({})


@app.route('/judge/datalist', 'judge_datalist')
class JudgeDataListView(base.Handler):
  @base.get_argument
  @base.sanitize
  async def get(self, last: int):
    # TODO(iceboy): This function looks strange.
    # Judge will have PRIV_READ_PROBLEM_DATA, domain administrator will have PERM_READ_PROBLEM_DATA.
    if not self.has_priv(builtin.PRIV_READ_PROBLEM_DATA):
      self.check_perm(builtin.PERM_READ_PROBLEM_DATA)
    pids = await problem.get_data_list(last)
    datalist = []
    for did, pid in pids:
      datalist.append({'domain_id': did, 'pid': pid})
    self.json({'list': datalist, 'time': int(time.time())})


@app.connection_route('/judge/consume-conn', 'judge_consume-conn')
class JudgeNotifyConnection(base.Connection):
  @base.require_priv(builtin.PRIV_READ_RECORD_CODE | builtin.PRIV_WRITE_RECORD)
  async def on_open(self):
    self.rids = {}  # delivery_tag -> rid
    self.channel = await queue.consume('judge', self._on_queue_message)
    asyncio.ensure_future(self.channel.close_event.wait()).add_done_callback(lambda _: self.close())

  async def _on_queue_message(self, tag, *, rid):
    # This callback runs in the receiver loop of the amqp connection. Should not block here.
    async def start():
      # TODO(iceboy): Error handling?
      rdoc = await record.begin_judge(rid, self.user['_id'], self.id, constant.record.STATUS_COMPILING)
      if rdoc:
        self.rids[tag] = rdoc['_id']
        self.send(id=str(rdoc['_id']), tag=tag, pid=str(rdoc['pid']), domain_id=rdoc['domain_id'],
                  lang=rdoc['lang'], code=rdoc['code'], type=rdoc['type'])
        await bus.publish('record_change', rdoc['_id'])
      else:
        # Record not found, eat it.
        await self.channel.basic_client_ack(tag)

    asyncio.get_event_loop().create_task(start())

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
        }
      await record.next_judge(rid, self.user['_id'], self.id, **update)
      await bus.publish('record_change', rid)
    elif key == 'end':
      rid = self.rids.pop(tag)
      rdoc, _ = await asyncio.gather(record.end_judge(rid, self.user['_id'], self.id,
                                                      int(kwargs['status']),
                                                      int(kwargs['score']),
                                                      int(kwargs['time_ms']),
                                                      int(kwargs['memory_kb'])),
                                     self.channel.basic_client_ack(tag))
      accept = True if rdoc['status'] == constant.record.STATUS_ACCEPTED else False
      post_coros = [bus.publish('record_change', rid)]
      if rdoc['type'] == constant.record.TYPE_SUBMISSION:
        _, delta_submit, delta_new = (
          await problem.update_status(rdoc['domain_id'], rdoc['pid'], rdoc['uid'],
                                      rdoc['_id'], rdoc['status'], accept, rdoc['score']))
        if delta_submit != 0 or delta_new != 0:
          post_coros.append(problem.inc(rdoc['domain_id'], rdoc['pid'], delta_submit, delta_new))
          # TODO(twd2): update user (num_submit, num_accept)
        if rdoc['tid']:
          post_coros.append(contest.update_status(rdoc['domain_id'], rdoc['tid'], rdoc['uid'],
                                                  rdoc['_id'], rdoc['pid'], accept, rdoc['score']))
        if accept:
          post_coros.append(training.update_status_by_pid(rdoc['domain_id'],
                                                          rdoc['uid'], rdoc['pid']))
      await asyncio.gather(*post_coros)
    elif key == 'nack':
      await self.channel.basic_client_nack(tag)

  async def on_close(self):
    async def close():
      await asyncio.gather(*[record.end_judge(rid, self.user['_id'], self.id,
                                              constant.record.STATUS_CANCELED, 0, 0, 0)
                             for rid in self.rids.values()])
      await asyncio.gather(*[bus.publish('record_change', rid)
                             for rid in self.rids.values()])
      # There is a bug in current version's aioamqp and we cannot use no_wait=True here.
      await self.channel.close()

    asyncio.get_event_loop().create_task(close())
