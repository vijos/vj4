import asyncio
import functools
from vj4 import app
from vj4.controller import problem
from vj4.view import base
from vj4.model import builtin
from vj4.model import bus
from vj4.model import document
from vj4.model import record
from vj4.model import queue

@app.route('/p', 'problem_main')
class ProblemMainView(base.OperationView):
  PROBLEMS_PER_PAGE = 100

  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.get_argument
  @base.sanitize
  async def get(self, *, page: int=1):
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

@app.route('/p/{pid}', 'problem_detail')
class ProblemDetailView(base.View):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    path_components = self.build_path(('problem_main', self.reverse_url('problem_main')),
                                      (pdoc['title'], None))
    self.render('problem_detail.html', pdoc=pdoc,
                page_title=pdoc['title'], path_components=path_components)

@app.route('/p/{pid}/submit', 'problem_submit')
class ProblemDetailView(base.View):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    path_components = self.build_path(('problem_main', self.reverse_url('problem_main')),
                                      (pdoc['title'], None))
    self.render('problem_submit.html', pdoc=pdoc,
                page_title=pdoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str):
    pdoc = await problem.get(self.domain_id, pid)
    rid = await record.add(self.domain_id, pdoc['doc_id'], self.user['_id'], lang, code)
    await asyncio.gather(queue.publish('judge', rid=rid), bus.publish('record_change', rid))
    self.json_or_redirect(self.reverse_url('record_main'))

@app.route(r'/p/{pid}/solution', 'problem_solution')
class ProblemSolutionView(base.OperationView):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM_SOLUTION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    pdoc = await problem.get(self.domain_id, pid)
    psdocs = await problem.get_list_solution(self.domain_id, pdoc['doc_id'])
    path_components = self.build_path(
        ('problem_main', self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        ('problem_solution', None))
    self.render('problem_solution.html', psdocs=psdocs, path_components=path_components)

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
class ProblemDataView(base.View):
  @base.route_argument
  @base.sanitize
  async def stream_data(self, *, pid: document.convert_doc_id, headers_only: bool=False):
    # Judge will have PRIV_READ_PROBLEM_DATA, domain administrator will have PERM_READ_PROBLEM_DATA.
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
