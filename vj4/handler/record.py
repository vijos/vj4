import asyncio
import io
import zipfile

from aiohttp import web
from bson import objectid

from vj4 import app
from vj4 import error
from vj4.model import builtin
from vj4.model import document
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
    rdocs = await record.get_all_multi().sort([('_id', -1)]).to_list(50)
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
    self.send(html=self.render_html('record_tr.html', rdoc=rdoc), rdoc=rdoc)

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


@app.route('/records/{rid}/pretest_data', 'record_pretest_data')
class RecordPretestDataView(base.Handler):
  @base.require_priv(builtin.PRIV_READ_PRETEST_DATA)
  @base.route_argument
  @base.sanitize
  async def get(self, *, rid: objectid.ObjectId):
    rdoc = await record.get(rid)
    if not rdoc:
      raise error.RecordNotFoundError(rid)
    ddoc = await document.get(rdoc['domain_id'], document.TYPE_PRETEST_DATA, rdoc['data_id'])
    if not ddoc:
      raise error.ProblemDataNotFoundError(rdoc['pid'])

    output_buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(output_buffer, 'a', zipfile.ZIP_DEFLATED)
    config_content = str(len(ddoc['data_input'])) + "\n"
    for i, (data_input, data_output) in enumerate(zip(ddoc['data_input'], ddoc['data_output'])):
      input_file = 'input{0}.txt'.format(i)
      output_file = 'output{0}.txt'.format(i)
      config_content += '{0}|{1}|1|10|1024\n'.format(input_file, output_file)
      zip_file.writestr('Input/{0}'.format(input_file), data_input)
      zip_file.writestr('Output/{0}'.format(output_file), data_output)
    zip_file.writestr('Config.ini', config_content)

    # mark all files as created in Windows
    for zfile in zip_file.filelist:
      zfile.create_system = 0

    zip_file.close()
    await self.binary(output_buffer.getvalue())
