import asyncio
import calendar
import datetime
import io
import struct
import zipfile
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.handler import base
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.service import bus


@app.route('/records', 'record_main')
class RecordMainHandler(base.Handler):
  async def get(self):
    # TODO(iceboy): projection, pagination.
    rdocs = await record.get_all_multi(
      get_hidden=self.has_priv(builtin.PRIV_VIEW_HIDDEN_RECORD)).sort([('_id', -1)]).to_list(50)
    # TODO(iceboy): projection.
    udict, pdict = await asyncio.gather(
        user.get_dict(rdoc['uid'] for rdoc in rdocs),
        problem.get_dict((rdoc['domain_id'], rdoc['pid']) for rdoc in rdocs))
    # statistics
    statistics = None
    if self.has_priv(builtin.PRIV_VIEW_JUDGE_STATISTICS):
      ts = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
      day_count, week_count, month_count, year_count, rcount = await asyncio.gather(
          record.get_count(objectid.ObjectId(
              struct.pack('>i', ts - 24 * 3600) + struct.pack('b', -1) * 8)),
          record.get_count(objectid.ObjectId(
              struct.pack('>i', ts - 7 * 24 * 3600) + struct.pack('b', -1) * 8)),
          record.get_count(objectid.ObjectId(
              struct.pack('>i', ts - 30 * 24 * 3600) + struct.pack('b', -1) * 8)),
          record.get_count(objectid.ObjectId(
              struct.pack('>i', ts - int(365.2425 * 24 * 3600)) + struct.pack('b', -1) * 8)),
          record.get_count())
      statistics = {'day': day_count, 'week': week_count, 'month': month_count,
                    'year': year_count, 'total': rcount}
    self.render('record_main.html', rdocs=rdocs, udict=udict, pdict=pdict, statistics=statistics)


@app.connection_route('/records-conn', 'record_main-conn')
class RecordMainConnection(base.Connection):
  async def on_open(self):
    await super(RecordMainConnection, self).on_open()
    bus.subscribe(self.on_record_change, ['record_change'])

  async def on_record_change(self, e):
    rdoc = await record.get(objectid.ObjectId(e['value']), record.PROJECTION_PUBLIC)
    # check permission for visibility: contest
    if rdoc['tid']:
      now = datetime.datetime.utcnow()
      tdoc = await contest.get(rdoc['domain_id'], rdoc['tid'])
      if (not contest.RULES[tdoc['rule']].show_func(tdoc, now)
          and (self.domain_id != tdoc['domain_id']
               or not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS))):
        return
    # TODO(iceboy): join from event to improve performance?
    # TODO(iceboy): projection.
    udoc, pdoc = await asyncio.gather(user.get_by_uid(rdoc['uid']),
                                      problem.get(rdoc['domain_id'], rdoc['pid']))
    # check permission for visibility: hidden problem
    if pdoc.get('hidden', False) and (pdoc['domain_id'] != self.domain_id
                                      or not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)):
      pdoc = None
    self.send(html=self.render_html('record_main_tr.html', rdoc=rdoc, udoc=udoc, pdoc=pdoc))

  async def on_close(self):
    bus.unsubscribe(self.on_record_change)


@app.route('/records/{rid}', 'record_detail')
class RecordDetailHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, rid: objectid.ObjectId):
    rdoc = await record.get(rid)
    if not rdoc:
      raise error.RecordNotFoundError(rid)
    # TODO(iceboy): Check domain permission, permission for visibility in place.
    if rdoc['domain_id'] != self.domain_id:
      self.redirect(self.reverse_url('record_detail', rid=rid, domain_id=rdoc['domain_id']))
      return
    # check permission for visibility: contest
    show_status = True
    if rdoc['tid']:
      now = datetime.datetime.utcnow()
      tdoc = await contest.get(rdoc['domain_id'], rdoc['tid'])
      show_status = contest.RULES[tdoc['rule']].show_func(tdoc, now) \
                    or self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)
    # TODO(twd2): futher check permission for visibility.
    if (not self.own(rdoc, field='uid')
        and not self.has_perm(builtin.PERM_READ_RECORD_CODE)
        and not self.has_priv(builtin.PRIV_READ_RECORD_CODE)):
      del rdoc['code']
    if not show_status and 'code' not in rdoc:
      raise error.PermissionError(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS)
    udoc, dudoc, pdoc = await asyncio.gather(
        user.get_by_uid(rdoc['uid']),
        domain.get_user(self.domain_id, rdoc['uid']),
        problem.get(rdoc['domain_id'], rdoc['pid']))
    if show_status and 'judge_uid' in rdoc:
      judge_udoc = await user.get_by_uid(rdoc['judge_uid'])
    else:
      judge_udoc = None
    # check permission for visibility: hidden problem
    if pdoc.get('hidden', False) and not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      pdoc = None
    self.render('record_detail.html', rdoc=rdoc, udoc=udoc, dudoc=dudoc, pdoc=pdoc,
                judge_udoc=judge_udoc, show_status=show_status)


@app.route('/records/{rid}/rejudge', 'record_rejudge')
class RecordRejudgeHandler(base.Handler):
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, rid: objectid.ObjectId):
    rdoc = await record.get(rid)
    if rdoc['domain_id'] == self.domain_id:
      self.check_perm(builtin.PERM_REJUDGE)
    else:
      self.check_priv(builtin.PRIV_REJUDGE)
    await record.rejudge(rdoc['_id'])
    self.json_or_redirect(self.referer_or_main)


@app.route('/records/{rid}/data', 'record_pretest_data')
class RecordPretestDataHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, rid: objectid.ObjectId):
    rdoc = await record.get(rid)
    if not rdoc or rdoc['type'] != constant.record.TYPE_PRETEST:
      raise error.RecordNotFoundError(rid)
    if not self.own(rdoc, builtin.PRIV_READ_PRETEST_DATA_SELF, 'uid'):
      self.check_priv(builtin.PRIV_READ_PRETEST_DATA)
    ddoc = await document.get(rdoc['domain_id'], document.TYPE_PRETEST_DATA, rdoc['data_id'])
    if not ddoc:
      raise error.RecordDataNotFoundError(rdoc['_id'])

    output_buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(output_buffer, 'a', zipfile.ZIP_DEFLATED)
    config_content = str(len(ddoc['content'])) + '\n'
    for i, (data_input, data_output) in enumerate(ddoc['content']):
      input_file = 'input{0}.txt'.format(i)
      output_file = 'output{0}.txt'.format(i)
      config_content += '{0}|{1}|1|10|262144\n'.format(input_file, output_file)
      zip_file.writestr('Input/{0}'.format(input_file), data_input)
      zip_file.writestr('Output/{0}'.format(output_file), data_output)
    zip_file.writestr('Config.ini', config_content)
    # mark all files as created in Windows :p
    for zfile in zip_file.filelist:
      zfile.create_system = 0
    zip_file.close()

    await self.binary(output_buffer.getvalue(), 'application/zip')
