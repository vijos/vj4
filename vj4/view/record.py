import asyncio
from bson import objectid
from vj4 import app
from vj4.controller import problem
from vj4.model import bus
from vj4.model import record
from vj4.model import user
from vj4.view import base

STATUS_TEXTS = {
  record.STATUS_WAITING: 'Waiting',
  record.STATUS_ACCEPTED: 'Accepted',
  record.STATUS_WRONG_ANSWER: 'Wrong Answer',
  record.STATUS_TIME_LIMIT_EXCEEDED: 'Time Exceeded',
  record.STATUS_MEMORY_LIMIT_EXCEEDED: 'Memory Exceeded',
  record.STATUS_OUTPUT_LIMIT_EXCEEDED: 'Output Exceeded',
  record.STATUS_RUNTIME_ERROR: 'Runtime Error',
  record.STATUS_COMPILE_ERROR: 'Compile Error',
  record.STATUS_SYSTEM_ERROR: 'System Error',
  record.STATUS_CANCELED: 'Cancelled',
  record.STATUS_ETC: 'Unknown Error',
  record.STATUS_JUDGING: 'Running',
  record.STATUS_COMPILING: 'Compiling',
  record.STATUS_IGNORED: 'Ignored',
}

STATUS_CODES = {
  record.STATUS_WAITING: 'pending',
  record.STATUS_ACCEPTED: 'pass',
  record.STATUS_WRONG_ANSWER: 'fail',
  record.STATUS_TIME_LIMIT_EXCEEDED: 'fail',
  record.STATUS_MEMORY_LIMIT_EXCEEDED: 'fail',
  record.STATUS_OUTPUT_LIMIT_EXCEEDED: 'fail',
  record.STATUS_RUNTIME_ERROR: 'fail',
  record.STATUS_COMPILE_ERROR: 'fail',
  record.STATUS_SYSTEM_ERROR: 'fail',
  record.STATUS_CANCELED: 'ignored',
  record.STATUS_ETC: 'fail',
  record.STATUS_JUDGING: 'progress',
  record.STATUS_COMPILING: 'progress',
  record.STATUS_IGNORED: 'ignored',
}

@app.route('/records', 'record_main')
class RecordMainView(base.View):
  async def get(self):
    # TODO(iceboy): projection, pagination.
    rdocs = await record.get_multi().sort([('_id', -1)]).to_list(50)
    await asyncio.gather(user.attach_udocs(rdocs, 'uid'),
                         problem.attach_pdocs(rdocs, 'domain_id', 'pid'))
    self.render('record_main.html', rdocs=rdocs)

@app.connection_route('/records-conn', 'record_main-conn')
class RecordMainConnection(base.Connection):
  async def on_open(self):
    await super(RecordMainConnection, self).on_open()
    bus.subscribe(self.on_record_change, ['record_change'])

  async def on_record_change(self, e):
    rdoc = await record.get(objectid.ObjectId(e['value']))
    # TODO(iceboy): get uname, ugravatar and pname from event.
    # TODO(iceboy): check permission for visibility. (e.g. test).
    self.send(html=self.render_html('record_tr.html', rdoc=rdoc))

  async def on_close(self):
    bus.unsubscribe(self.on_record_change)

@app.route('/records/{rid}', 'record_detail')
class RecordDetailView(base.View):
  @base.route_argument
  async def get(self, *, rid):
    rdoc = await record.get(objectid.ObjectId(rid))
    # TODO(iceboy): join uname, ugravatar and pname.
    self.render('record_detail.html', rdoc=rdoc)
