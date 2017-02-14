import asyncio
import datetime
import functools
import hashlib
from bson import objectid

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4 import job
from vj4.handler import base
from vj4.model import builtin
from vj4.model import user
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.model import opcount
from vj4.model import record
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.model.adaptor import training
from vj4.service import bus
from vj4.util import pagination


@app.route('/p', 'problem_main')
class ProblemMainHandler(base.OperationHandler):
  PROBLEMS_PER_PAGE = 100

  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.get_argument
  @base.sanitize
  async def get(self, *, page: int=1):
    # TODO(iceboy): projection.
    if not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      f = {'hidden': False}
    else:
      f = {}
    pdocs, ppcount, pcount = await pagination.paginate(problem.get_multi(domain_id=self.domain_id,
                                                                         **f) \
                                                              .sort([('doc_id', 1)]),
                                                       page, self.PROBLEMS_PER_PAGE)
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      # TODO(iceboy): projection.
      psdict = await problem.get_dict_status(self.domain_id,
                                             self.user['_id'],
                                             (pdoc['doc_id'] for pdoc in pdocs))
    else:
      psdict = None
    self.render('problem_main.html', page=page, ppcount=ppcount, pcount=pcount, pdocs=pdocs,
                psdict=psdict, categories=problem.get_categories())

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def star_unstar(self, *, pid: document.convert_doc_id, star: bool):
    pdoc = await problem.get(self.domain_id, pid)
    pdoc = await problem.set_star(self.domain_id, pdoc['doc_id'], self.user['_id'], star)
    self.json_or_redirect(self.url, star=pdoc['star'])

  post_star = functools.partialmethod(star_unstar, star=True)
  post_unstar = functools.partialmethod(star_unstar, star=False)


@app.route('/p/{pid:-?\d+|\w{24}}', 'problem_detail')
class ProblemDetailHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    udoc = await user.get_by_uid(pdoc['owner_uid'])
    tdocs = await training.get_multi(self.domain_id, **{'dag.pids': pid}).to_list(None) \
            if self.has_perm(builtin.PERM_VIEW_TRAINING) else None
    ctdocs = await contest.get_multi(self.domain_id, pids=pid).to_list(None) \
             if self.has_perm(builtin.PERM_VIEW_CONTEST) else None
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], None))
    self.render('problem_detail.html', pdoc=pdoc, udoc=udoc, tdocs=tdocs, ctdocs=ctdocs,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/p/{pid}/submit', 'problem_submit')
class ProblemSubmitHandler(base.Handler):
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    # TODO(twd2): check status, eg. test, hidden problem, ...
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    udoc = await user.get_by_uid(pdoc['owner_uid'])
    if uid == None:
      rdocs = []
    else:
      # TODO(iceboy): needs to be in sync with contest_detail_problem_submit
      rdocs = await record \
          .get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id']) \
          .sort([('_id', -1)]) \
          .to_list(10)
    if not self.prefer_json:
      path_components = self.build_path(
          (self.translate('problem_main'), self.reverse_url('problem_main')),
          (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
          (self.translate('problem_submit'), None))
      self.render('problem_submit.html', pdoc=pdoc, udoc=udoc, rdocs=rdocs,
                  page_title=pdoc['title'], path_components=path_components)
    else:
      self.json({'rdocs': rdocs})

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str):
    await opcount.inc(**opcount.OPS['run_code'], ident=opcount.PREFIX_USER + str(self.user['_id']))
    # TODO(twd2): check status, eg. test, hidden problem, ...
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION,
                           self.user['_id'], lang, code)
    self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/p/{pid}/pretest', 'problem_pretest')
class ProblemPretestHandler(base.Handler):
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str,
                 data_input: str, data_output: str):
    await opcount.inc(**opcount.OPS['run_code'], ident=opcount.PREFIX_USER + str(self.user['_id']))
    pdoc = await problem.get(self.domain_id, pid)
    # don't need to check hidden status
    content = list(zip(self.request.POST.getall('data_input'),
                       self.request.POST.getall('data_output')))
    did = await document.add(self.domain_id, content, self.user['_id'], document.TYPE_PRETEST_DATA,
                             pid=pdoc['doc_id'])
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_PRETEST,
                           self.user['_id'], lang, code, did)
    self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.connection_route('/p/{pid}/pretest-conn', 'problem_pretest-conn')
class ProblemPretestConnection(base.Connection):
  async def on_open(self):
    await super(ProblemPretestConnection, self).on_open()
    self.pid = document.convert_doc_id(self.request.match_info['pid'])
    bus.subscribe(self.on_record_change, ['record_change'])

  async def on_record_change(self, e):
    rdoc = await record.get(objectid.ObjectId(e['value']), record.PROJECTION_PUBLIC)
    if rdoc['uid'] != self.user['_id'] or \
       rdoc['domain_id'] != self.domain_id or rdoc['pid'] != self.pid:
      return
    # check permission for visibility: contest
    if rdoc['tid']:
      now = datetime.datetime.utcnow()
      tdoc = await contest.get(rdoc['domain_id'], rdoc['tid'])
      if (not contest.RULES[tdoc['rule']].show_func(tdoc, now)
          and (self.domain_id != tdoc['domain_id']
               or not self.has_perm(builtin.PERM_VIEW_CONTEST_HIDDEN_STATUS))):
        return
    # TODO(iceboy): join from event to improve performance?
    self.send(rdoc=rdoc)

  async def on_close(self):
    bus.unsubscribe(self.on_record_change)


@app.route('/p/{pid}/solution', 'problem_solution')
class ProblemSolutionHandler(base.OperationHandler):
  SOLUTIONS_PER_PAGE = 20

  @base.require_perm(builtin.PERM_VIEW_PROBLEM_SOLUTION)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id, page: int=1):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdocs, pcount, pscount = await pagination.paginate(
        problem.get_multi_solution(self.domain_id, pdoc['doc_id']),
        page, self.SOLUTIONS_PER_PAGE)
    uids = {pdoc['owner_uid']}
    uids.update(psdoc['owner_uid'] for psdoc in psdocs)
    for psdoc in psdocs:
      if 'reply' in psdoc:
        uids.update(psrdoc['owner_uid'] for psrdoc in psdoc['reply'])
    udict, dudict, pssdict = await asyncio.gather(
        user.get_dict(uids),
        domain.get_dict_user_by_uid(self.domain_id, uids),
        problem.get_dict_solution_status(
            self.domain_id, (psdoc['doc_id'] for psdoc in psdocs), self.user['_id']))
    dudict[self.user['_id']] = self.domain_user
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_solution'), None))
    self.render('problem_solution.html', path_components=path_components,
                pdoc=pdoc, psdocs=psdocs, page=page, pcount=pcount, pscount=pscount,
                udict=udict, dudict=dudict, pssdict=pssdict)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_PROBLEM_SOLUTION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_submit(self, *, pid: document.convert_doc_id, content: str):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    await problem.add_solution(self.domain_id, pdoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_edit_solution(self, *, pid: document.convert_doc_id,
                               psid: document.convert_doc_id, content: str):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    if not self.own(psdoc, builtin.PERM_EDIT_PROBLEM_SOLUTION_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM_SOLUTION)
    psdoc = await problem.set_solution(self.domain_id, psdoc['doc_id'],
                                       content=content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_solution(self, *, pid: document.convert_doc_id,
                                 psid: document.convert_doc_id):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    if not self.own(psdoc, builtin.PERM_DELETE_PROBLEM_SOLUTION_SELF):
      self.check_perm(builtin.PERM_DELETE_PROBLEM_SOLUTION)
    psdoc = await problem.delete_solution(self.domain_id, psdoc['doc_id'])
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_edit_reply(self, *, pid: document.convert_doc_id,
                            psid: document.convert_doc_id, psrid: document.convert_doc_id,
                            content: str):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc, psrdoc = await problem.get_solution_reply(self.domain_id, psid, psrid)
    if not psdoc or psdoc['parent_doc_id'] != pdoc['doc_id']:
      raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
    if not self.own(psrdoc, builtin.PERM_EDIT_PROBLEM_SOLUTION_REPLY_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM_SOLUTION_REPLY)
    await problem.edit_solution_reply(self.domain_id, psid, psrid, content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_reply(self, *, pid: document.convert_doc_id,
                            psid: document.convert_doc_id, psrid: document.convert_doc_id):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc, psrdoc = await problem.get_solution_reply(self.domain_id, psid, psrid)
    if not psdoc or psdoc['parent_doc_id'] != pdoc['doc_id']:
      raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
    if not self.own(psrdoc, builtin.PERM_DELETE_PROBLEM_SOLUTION_REPLY_SELF):
      self.check_perm(builtin.PERM_DELETE_PROBLEM_SOLUTION_REPLY)
    await problem.delete_solution_reply(self.domain_id, psid, psrid, content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VOTE_PROBLEM_SOLUTION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def upvote_downvote(self, *,
                            pid: document.convert_doc_id,
                            psid: document.convert_doc_id,
                            value: int):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    psdoc, pssdoc = await problem.vote_solution(self.domain_id, psdoc['doc_id'],
                                                self.user['_id'], value)
    self.json_or_redirect(self.url, vote=psdoc['vote'], user_vote=pssdoc['vote'])

  post_upvote = functools.partialmethod(upvote_downvote, value=1)
  post_downvote = functools.partialmethod(upvote_downvote, value=-1)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_REPLY_PROBLEM_SOLUTION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_reply(self, *,
                       pid: document.convert_doc_id,
                       psid: document.convert_doc_id,
                       content: str):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    await problem.reply_solution(self.domain_id, psdoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.url)


@app.route('/p/{pid}/solution/{psid:\w{24}}/raw', 'problem_solution_raw')
class ProblemSolutionRawHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM_SOLUTION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id, psid: document.convert_doc_id):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    self.response.content_type = 'text/markdown'
    self.response.text = psdoc['content']


@app.route('/p/{pid}/solution/{psid:\w{24}}/{psrid:\w{24}}/raw', 'problem_solution_reply_raw')
class ProblemSolutionReplyRawHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM_SOLUTION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id, psid: document.convert_doc_id,
                psrid: objectid.ObjectId):
    pdoc = await problem.get(self.domain_id, pid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    psdoc, psrdoc = await problem.get_solution_reply(self.domain_id, psid, psrid)
    if not psdoc or psdoc['parent_doc_id'] != pdoc['doc_id']:
      raise error.DocumentNotFoundError(domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
    self.response.content_type = 'text/markdown'
    self.response.text = psrdoc['content']


@app.route('/p/{pid}/data', 'problem_data')
class ProblemDataHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def stream_data(self, *, pid: document.convert_doc_id, headers_only: bool=False):
    # Judges will have PRIV_READ_PROBLEM_DATA,
    # domain administrators will have PERM_READ_PROBLEM_DATA,
    # problem owner will have PERM_READ_PROBLEM_DATA_SELF.
    pdoc = await problem.get(self.domain_id, pid)
    if (not self.own(pdoc, builtin.PERM_READ_PROBLEM_DATA_SELF)
        and not self.has_perm(builtin.PERM_READ_PROBLEM_DATA)):
      self.check_priv(builtin.PRIV_READ_PROBLEM_DATA)
    grid_out = await problem.get_data(self.domain_id, pid)

    self.response.content_type = grid_out.content_type or 'application/zip'
    self.response.last_modified = grid_out.upload_date
    self.response.headers['Etag'] = '"{0}"'.format(grid_out.md5)
    # TODO(iceboy): Handle If-Modified-Since & If-None-Match here.
    self.response.content_length = grid_out.length

    if not headers_only:
      await self.response.prepare(self.request)
      # TODO(twd2): Range
      remaining = grid_out.length
      chunk = await grid_out.readchunk()
      while chunk and remaining >= len(chunk):
        self.response.write(chunk)
        remaining -= len(chunk)
        _, chunk = await asyncio.gather(self.response.drain(), grid_out.readchunk())
      if chunk:
        self.response.write(chunk[:remaining])
        await self.response.drain()
      await self.response.write_eof()

  head = functools.partialmethod(stream_data, headers_only=True)
  get = stream_data


@app.route('/p/create', 'problem_create')
class ProblemCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_PROBLEM)
  async def get(self):
    self.render('problem_edit.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_PROBLEM)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, title: str, content: str, hidden: bool=False):
    pid = await problem.add(self.domain_id, title, content, self.user['_id'],
                            hidden=hidden)
    self.json_or_redirect(self.reverse_url('problem_settings', pid=pid))


@app.route('/p/{pid}/edit', 'problem_edit')
class ProblemEditHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    udoc = await user.get_by_uid(pdoc['owner_uid'])
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_edit'), None))
    self.render('problem_edit.html', pdoc=pdoc, udoc=udoc,
                page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, title: str, content: str):
    pdoc = await problem.get(self.domain_id, pid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    await problem.edit(self.domain_id, pdoc['doc_id'], title=title, content=content)
    self.json_or_redirect(self.reverse_url('problem_detail', pid=pid))


@app.route('/p/{pid}/settings', 'problem_settings')
class ProblemSettingsHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    udoc = await user.get_by_uid(pdoc['owner_uid'])
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_settings'), None))
    self.render('problem_settings.html', pdoc=pdoc, udoc=udoc,
                page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, hidden: bool=False,
                 difficulty_setting: int, difficulty_admin: str=''):
    pdoc = await problem.get(self.domain_id, pid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    if difficulty_setting not in problem.SETTING_DIFFICULTY_RANGE:
        raise error.ValidationError('difficulty_setting')
    if difficulty_admin:
        try:
          difficulty_admin = int(difficulty_admin)
        except ValueError:
          raise error.ValidationError('difficulty_admin')
    else:
      difficulty_admin = None
    await problem.edit(self.domain_id, pdoc['doc_id'], hidden=hidden,
                       difficulty_setting=difficulty_setting, difficulty_admin=difficulty_admin)
    await job.difficulty.update_problem(self.domain_id, pdoc['doc_id'])
    self.json_or_redirect(self.reverse_url('problem_detail', pid=pid))


@app.route('/p/{pid}/upload', 'problem_upload')
class ProblemSettingsHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    pdoc = await problem.get(self.domain_id, pid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    if (not self.own(pdoc, builtin.PERM_READ_PROBLEM_DATA_SELF)
        and not self.has_perm(builtin.PERM_READ_PROBLEM_DATA)):
      self.check_priv(builtin.PRIV_READ_PROBLEM_DATA)
    self.render('problem_upload.html', pdoc=pdoc)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, file: lambda _: _):
    pdoc = await problem.get(self.domain_id, pid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    if (not self.own(pdoc, builtin.PERM_READ_PROBLEM_DATA_SELF)
        and not self.has_perm(builtin.PERM_READ_PROBLEM_DATA)):
      self.check_priv(builtin.PRIV_READ_PROBLEM_DATA)
    if file:
      data = file.file.read()
      md5 = hashlib.md5(data).hexdigest()
      fid = await fs.link_by_md5(md5)
      if not fid:
        fid = await fs.add_data(data)
      if pdoc.get('data'):
        await fs.unlink(pdoc['data'])
      await problem.set_data(self.domain_id, pid, fid)
    self.json_or_redirect(self.url)


@app.route('/p/{pid}/statistics', 'problem_statistics')
class ProblemStatisticsHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    # TODO(twd2)
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    udoc = await user.get_by_uid(pdoc['owner_uid'])
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_statistics'), None))
    self.render('problem_statistics.html', pdoc=pdoc, udoc=udoc,
                page_title=pdoc['title'], path_components=path_components)
