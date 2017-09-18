import asyncio
import calendar
import datetime
import struct
import urllib.parse
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4.handler import base
from vj4.handler import contest as contest_handler
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.service import bus
from vj4.util import options


class RecordVisibilityMixin(contest_handler.ContestVisibilityMixin):
  async def rdoc_contest_visible(self, rdoc):
    tdoc = await contest.get(rdoc['domain_id'], {'$in': [document.TYPE_CONTEST, document.TYPE_HOMEWORK]}, rdoc['tid'])
    return self.can_show_record(tdoc), tdoc


class RecordCommonOperationMixin(object):
  async def get_filter_query(self, uid_or_name, pid, tid):
    query = dict()
    if uid_or_name:
      try:
        query['uid'] = int(uid_or_name)
      except ValueError:
        udoc = await user.get_by_uname(uid_or_name)
        if not udoc:
          raise error.UserNotFoundError(uid_or_name) from None
        query['uid'] = udoc['_id']
    if pid or tid:
      query['domain_id'] = self.domain_id
      if pid:
        query['pid'] = document.convert_doc_id(pid)
      if tid:
        query['tid'] = document.convert_doc_id(tid)
    return query


class RecordMixin(RecordVisibilityMixin, RecordCommonOperationMixin):
  pass


@app.route('/records', 'record_main')
class RecordMainHandler(RecordMixin, base.Handler):
  @base.get_argument
  @base.sanitize
  async def get(self, *, start: str='', uid_or_name: str='', pid: str='', tid: str=''):
    if not self.has_priv(builtin.PRIV_VIEW_JUDGE_STATISTICS):
      start = ''
    if start:
      start = objectid.ObjectId(start)
    else:
      start = None
    query = await self.get_filter_query(uid_or_name, pid, tid)
    # TODO(iceboy): projection, pagination.
    rdocs = await record.get_all_multi(**query, end_id=start,
      get_hidden=self.has_priv(builtin.PRIV_VIEW_HIDDEN_RECORD)).sort([('_id', -1)]).limit(50).to_list()
    # TODO(iceboy): projection.
    udict, pdict = await asyncio.gather(
        user.get_dict(rdoc['uid'] for rdoc in rdocs),
        problem.get_dict_multi_domain((rdoc['domain_id'], rdoc['pid']) for rdoc in rdocs))
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
    url_prefix = '/d/{}'.format(urllib.parse.quote(self.domain_id))
    query_string = urllib.parse.urlencode(
      [('uid_or_name', uid_or_name), ('pid', pid), ('tid', tid)])
    self.render('record_main.html', rdocs=rdocs, udict=udict, pdict=pdict, statistics=statistics,
                filter_uid_or_name=uid_or_name, filter_pid=pid, filter_tid=tid,
                socket_url=url_prefix + '/records-conn?' + query_string, # FIXME(twd2): magic
                query_string=query_string)


@app.connection_route('/records-conn', 'record_main-conn')
class RecordMainConnection(RecordMixin, base.Connection):
  @base.get_argument
  @base.sanitize
  async def on_open(self, *, uid_or_name: str='', pid: str='', tid: str=''):
    await super(RecordMainConnection, self).on_open()
    self.query = await self.get_filter_query(uid_or_name, pid, tid)
    bus.subscribe(self.on_record_change, ['record_change'])

  async def on_record_change(self, e):
    rdoc = e['value']
    for key, value in self.query.items():
      if rdoc[key] != value:
        return
    if rdoc['tid']:
      show_status, tdoc = await self.rdoc_contest_visible(rdoc)
      if not show_status:
        return
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
class RecordDetailHandler(RecordMixin, base.Handler):
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
    if rdoc['tid']:
      show_status, tdoc = await self.rdoc_contest_visible(rdoc)
    else:
      show_status, tdoc = True, None
    # TODO(twd2): futher check permission for visibility.
    if (not self.own(rdoc, field='uid')
        and not self.has_perm(builtin.PERM_READ_RECORD_CODE)
        and not self.has_priv(builtin.PRIV_READ_RECORD_CODE)):
      del rdoc['code']
    if not show_status and 'code' not in rdoc:
      raise error.PermissionError(builtin.PERM_VIEW_CONTEST_HIDDEN_SCOREBOARD)
    udoc, dudoc = await asyncio.gather(
        user.get_by_uid(rdoc['uid']),
        domain.get_user(self.domain_id, rdoc['uid']))
    try:
      pdoc = await problem.get(rdoc['domain_id'], rdoc['pid'])
    except error.ProblemNotFoundError:
      pdoc = {}
    if show_status and 'judge_uid' in rdoc:
      judge_udoc = await user.get_by_uid(rdoc['judge_uid'])
    else:
      judge_udoc = None
    # check permission for visibility: hidden problem
    if pdoc.get('hidden', False) and not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      pdoc = None
    url_prefix = '/d/{}'.format(urllib.parse.quote(self.domain_id))
    self.render('record_detail.html', rdoc=rdoc, udoc=udoc, dudoc=dudoc, pdoc=pdoc, tdoc=tdoc,
                judge_udoc=judge_udoc, show_status=show_status,
                socket_url=url_prefix + '/records/{}/conn'.format(rid)) # FIXME(twd2): magic


@app.connection_route('/records/{rid}/conn', 'record_detail-conn')
class RecordDetailConnection(RecordMixin, base.Connection):
  async def on_open(self):
    await super(RecordDetailConnection, self).on_open()
    self.rid = objectid.ObjectId(self.request.match_info['rid'])
    rdoc = await record.get(self.rid, record.PROJECTION_PUBLIC)
    if rdoc['tid']:
      show_status, tdoc = await self.rdoc_contest_visible(rdoc)
      if not show_status:
        self.close()
        return
    bus.subscribe(self.on_record_change, ['record_change'])
    self.send_record(rdoc)

  async def on_record_change(self, e):
    rdoc = e['value']
    if rdoc['_id'] != self.rid:
      return
    self.send_record(rdoc)

  def send_record(self, rdoc):
    self.send(status_html=self.render_html('record_detail_status.html', rdoc=rdoc),
              summary_html=self.render_html('record_detail_summary.html', rdoc=rdoc))

  async def on_close(self):
    bus.unsubscribe(self.on_record_change)


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
    if not rdoc.get('data_id'):
      raise error.RecordDataNotFoundError(rdoc['_id'])
    secret = await fs.get_secret(rdoc['data_id'])
    if not secret:
      raise error.RecordDataNotFoundError(rdoc['_id'])
    self.redirect(options.cdn_prefix.rstrip('/') + \
                  self.reverse_url('fs_get', domain_id=builtin.DOMAIN_ID_SYSTEM,
                                   secret=secret))
