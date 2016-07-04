import asyncio

from bson import objectid

from vj4 import app
from vj4 import error
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import problem
from vj4.service import bus
from vj4.handler import base


@app.route('/records', 'record_main')
class RecordMainView(base.Handler):
  async def get(self):
    # TODO(iceboy): projection, pagination.
    # TODO(twd2): check permission for visibility. (e.g. test).
    rdocs = await record.get_multi().sort([('_id', -1)]).to_list(50)
    # TODO(iceboy): projection.
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
    # TODO(iceboy): join from event to improve performance?
    # TODO(iceboy): projection.
    rdoc['udoc'], rdoc['pdoc'] = await asyncio.gather(
      user.get_by_uid(rdoc['uid']), problem.get(rdoc['domain_id'], rdoc['pid']))
    # TODO(iceboy): check permission for visibility. (e.g. test).
    self.send(html=self.render_html('record_tr.html', rdoc=rdoc))

  async def on_close(self):
    bus.unsubscribe(self.on_record_change)


@app.route('/records/{rid}', 'record_detail')
class RecordDetailView(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, rid: objectid.ObjectId):
    # TODO(twd2): check permission for visibility. (e.g. test).
    rdoc = await record.get(rid)
    if not rdoc:
      raise error.RecordNotFoundError(rid)
    rdoc['udoc'], rdoc['pdoc'] = await asyncio.gather(
      user.get_by_uid(rdoc['uid']), problem.get(rdoc['domain_id'], rdoc['pid']))
    self.render('record_detail.html', rdoc=rdoc)
