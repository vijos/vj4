import asyncio
import functools

from vj4 import app
from vj4 import error
from vj4 import constant
from vj4.model import builtin
from vj4.model import user
from vj4.model import document
from vj4.model import record
from vj4.model.adaptor import problem
from vj4.handler import base


@app.route('/p', 'problem_main')
class ProblemMainView(base.OperationHandler):
  PROBLEMS_PER_PAGE = 100

  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.get_argument
  @base.sanitize
  async def get(self, *, page: int = 1):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pcount, pdocs = await asyncio.gather(problem.count(self.domain_id),
                                         problem.get_list(self.domain_id, uid,
                                                          skip=(page - 1) * self.PROBLEMS_PER_PAGE,
                                                          limit=self.PROBLEMS_PER_PAGE))
    self.render('problem_main.html', page=page, pcount=pcount, pdocs=pdocs)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def star_unstar(self, *, pid: document.convert_doc_id, star: bool):
    pdoc = await problem.get(self.domain_id, pid)
    pdoc = await problem.set_star(self.domain_id, pdoc['doc_id'], self.user['_id'], star)
    self.json_or_redirect(self.referer_or_main, star=pdoc['star'])

  post_star = functools.partialmethod(star_unstar, star=True)
  post_unstar = functools.partialmethod(star_unstar, star=False)


@app.route('/p/{pid:-?\d+|\w{24}}', 'problem_detail')
class ProblemDetailView(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    await user.attach_udocs([pdoc], 'owner_uid')
    path_components = self.build_path(
      (self.translate('problem_main'), self.reverse_url('problem_main')),
      (pdoc['title'], None))
    self.render('problem_detail.html', pdoc=pdoc,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/p/{pid}/submit', 'problem_submit')
class ProblemSubmitView(base.Handler):
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    await user.attach_udocs([pdoc], 'owner_uid')
    if uid == None:
      rdocs = []
    else:
      # TODO(iceboy): needs to be in sync with contest_detail_problem_submit
      rdocs = await record \
          .get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id']) \
          .sort([('_id', -1)]) \
          .to_list(10)
    path_components = self.build_path(
      (self.translate('problem_main'), self.reverse_url('problem_main')),
      (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
      (self.translate('problem_submit'), None))
    self.json_or_render('problem_submit.html', pdoc=pdoc, rdocs=rdocs,
                        page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str):
    pdoc = await problem.get(self.domain_id, pid)
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_SUBMISSION, self.user['_id'],
                           lang, code)
    self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/p/{pid}/pretest', 'problem_pretest')
class ProblemPretestView(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM_SOLUTION)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str, data_input: str, data_output: str):
    tid = await document.add(self.domain_id, None, self.user['_id'], document.TYPE_PRETEST_DATA,
                             data_input = self.request.POST.getall('data_input'),
                             data_output = self.request.POST.getall('data_output'))
    # TODO(iceboy): Use pdoc['doc_id'] -- never trust user input.
    rid = await record.add(self.domain_id, pid, constant.record.TYPE_PRETEST, self.user['_id'],
                           lang, code, tid)
    self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.route('/p/{pid}/solution', 'problem_solution')
class ProblemSolutionView(base.OperationHandler):
  SOLUTIONS_PER_PAGE = 30

  @base.require_perm(builtin.PERM_VIEW_PROBLEM_SOLUTION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id, page: int = 1):
    skip = (page - 1) * self.SOLUTIONS_PER_PAGE
    limit = self.SOLUTIONS_PER_PAGE
    pdoc = await problem.get(self.domain_id, pid)
    psdocs = await problem.get_list_solution(self.domain_id, pdoc['doc_id'],
                                             skip=skip,
                                             limit=limit)
    psdocs_with_pdoc_and_reply = list(psdocs)
    psdocs_with_pdoc_and_reply.append(pdoc)
    for psdoc in psdocs:
      if 'reply' in psdoc:
        psdocs_with_pdoc_and_reply.extend(psdoc['reply'])
    await user.attach_udocs(psdocs_with_pdoc_and_reply, 'owner_uid')
    path_components = self.build_path(
      (self.translate('problem_main'), self.reverse_url('problem_main')),
      (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
      (self.translate('problem_solution'), None))
    self.render('problem_solution.html', pdoc=pdoc, psdocs=psdocs, path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM_SOLUTION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_submit(self, *, pid: document.convert_doc_id, content: str):
    pdoc = await problem.get(self.domain_id, pid)
    await problem.add_solution(self.domain_id, pdoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.reverse_url('problem_solution', pid=pdoc['doc_id']))

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
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    pssdoc = await problem.vote_solution(self.domain_id, psdoc['doc_id'], self.user['_id'], value)
    self.json_or_redirect(self.reverse_url('problem_solution', pid=pid), vote=pssdoc['vote'])

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
    psdoc = await problem.get_solution(self.domain_id, psid, pdoc['doc_id'])
    await problem.reply_solution(self.domain_id, psdoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.reverse_url('problem_solution', pid=pid))


@app.route('/p/{pid}/data', 'problem_data')
class ProblemDataView(base.Handler):
  @base.route_argument
  @base.sanitize
  async def stream_data(self, *, pid: document.convert_doc_id, headers_only: bool = False):
    # Judges will have PRIV_READ_PROBLEM_DATA, domain administrators will have PERM_READ_PROBLEM_DATA.
    if not self.has_priv(builtin.PRIV_READ_PROBLEM_DATA):
      self.check_perm(builtin.PERM_READ_PROBLEM_DATA)
    grid_out = await problem.get_data(self.domain_id, pid)

    self.response.content_type = grid_out.content_type or 'application/octet-stream'
    self.response.last_modified = grid_out.upload_date
    self.response.headers['Etag'] = '"%s"' % grid_out.md5
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
class ProblemCreateView(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_PROBLEM)
  async def get(self):
    self.render('problem_edit.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_PROBLEM)
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, title: str, content: str):
    pid = await problem.add(self.domain_id, title, content, self.user['_id'])
    self.json_or_redirect(self.reverse_url('problem_detail', pid=pid))


@app.route('/p/{pid}/edit', 'problem_edit')
class ProblemEditView(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    pdoc = await problem.get(self.domain_id, pid)
    if not pdoc:
      raise error.DiscussionNotFoundError(self.domain_id, pid)
    await user.attach_udocs([pdoc], 'owner_uid')
    path_components = self.build_path(
      (self.translate('problem_main'), self.reverse_url('problem_main')),
      (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
      (self.translate('problem_edit'), None))
    self.render('problem_edit.html', pdoc=pdoc,
                page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_EDIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, title: str, content: str):
    # TODO(twd2): new domain_id
    await problem.set(self.domain_id, pid, title=title, content=content)
    self.json_or_redirect(self.reverse_url('problem_detail', pid=pid))
