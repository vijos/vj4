import asyncio
import functools
import io
import os.path
import zipfile
from bson import objectid
from urllib import parse

from vj4 import app
from vj4 import constant
from vj4 import error
from vj4 import job
from vj4.handler import base
from vj4.handler import record as record_handler
from vj4.model import builtin
from vj4.model import user
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.model import oplog
from vj4.model import record
from vj4.model.adaptor import contest
from vj4.model.adaptor import problem
from vj4.model.adaptor import training
from vj4.service import bus
from vj4.util import pagination
from vj4.util import options


async def render_or_json_problem_list(self, page, ppcount, pcount, pdocs,
                                      category, psdict, **kwargs):
  if 'page_title' not in kwargs:
    kwargs['page_title'] = self.translate(self.TITLE)
  if 'path_components' not in kwargs:
    kwargs['path_components'] = self.build_path((self.translate(self.NAME), None))
  if self.prefer_json:
    list_html = self.render_html('partials/problem_list.html', page=page, ppcount=ppcount,
                                 pcount=pcount, pdocs=pdocs, psdict=psdict)
    stat_html = self.render_html('partials/problem_stat.html', pcount=pcount)
    lucky_html = self.render_html('partials/problem_lucky.html', category=category)
    path_html = self.render_html('partials/path.html', path_components=kwargs['path_components'])
    self.json({'title': self.render_title(kwargs['page_title']),
               'fragments': [{'html': list_html},
                             {'html': stat_html},
                             {'html': lucky_html},
                             {'html': path_html}]})
  else:
    self.render('problem_main.html', page=page, ppcount=ppcount, pcount=pcount, pdocs=pdocs,
                category=category, psdict=psdict, categories=problem.get_categories(),
                **kwargs)


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
    await render_or_json_problem_list(self, page=page, ppcount=ppcount, pcount=pcount,
                                      pdocs=pdocs, category='', psdict=psdict)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_csrf_token
  @base.sanitize
  async def star_unstar(self, *, pid: document.convert_doc_id, star: bool):
    pdoc = await problem.get(self.domain_id, pid)
    psdoc = await problem.set_star(self.domain_id, pdoc['doc_id'], self.user['_id'], star)
    self.json_or_redirect(self.referer_or_main, star=psdoc['star'])

  post_star = functools.partialmethod(star_unstar, star=True)
  post_unstar = functools.partialmethod(star_unstar, star=False)


@app.route('/p/random', 'problem_random')
class ProblemRandomHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self):
    if not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      f = {'hidden': False}
    else:
      f = {}
    pid = await problem.get_random_id(self.domain_id, **f)
    if not pid:
      raise error.NoProblemError()
    self.json_or_redirect(self.reverse_url('problem_detail', pid=pid), pid=pid)


@app.route('/p/category/{category:[^/]*}', 'problem_category')
class ProblemCategoryHandler(base.OperationHandler):
  PROBLEMS_PER_PAGE = 100

  @staticmethod
  def my_split(string, delim):
    return list(filter(lambda s: bool(s), map(lambda s: s.strip(), string.split(delim))))

  @staticmethod
  def build_query(query_string):
    category_groups = ProblemCategoryHandler.my_split(query_string, ' ')
    if not category_groups:
      return {}
    query = {'$or': []}
    for g in category_groups:
      categories = ProblemCategoryHandler.my_split(g, ',')
      if not categories:
        continue
      sub_query = {'$and': []}
      for c in categories:
        if c in builtin.PROBLEM_CATEGORIES \
           or c in builtin.PROBLEM_SUB_CATEGORIES:
          sub_query['$and'].append({'category': c})
        else:
          sub_query['$and'].append({'tag': c})
      query['$or'].append(sub_query)
    return query

  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, category: str, page: int=1):
    # TODO(iceboy): projection.
    if not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      f = {'hidden': False}
    else:
      f = {}
    query = ProblemCategoryHandler.build_query(category)
    pdocs, ppcount, pcount = await pagination.paginate(problem.get_multi(domain_id=self.domain_id,
                                                                         **query,
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
    page_title = category or self.translate('(All Problems)')
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (page_title, None))
    await render_or_json_problem_list(self, page=page, ppcount=ppcount, pcount=pcount,
                                      pdocs=pdocs, category=category, psdict=psdict,
                                      page_title=page_title, path_components=path_components)


@app.route('/p/category/{category:[^/]*}/random', 'problem_category_random')
class ProblemCategoryRandomHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, category: str):
    if not self.has_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN):
      f = {'hidden': False}
    else:
      f = {}
    query = ProblemCategoryHandler.build_query(category)
    pid = await problem.get_random_id(self.domain_id, **query, **f)
    if pid:
      self.json_or_redirect(self.reverse_url('problem_detail', pid=pid))
    else:
      self.json_or_redirect(self.referer_or_main)


@app.route('/p/{pid:-?\d+|\w{24}}', 'problem_detail')
class ProblemDetailHandler(base.Handler):
  async def _get_related_trainings(self, pid):
    if self.has_perm(builtin.PERM_VIEW_TRAINING):
      return await training.get_multi(self.domain_id, **{'dag.pids': pid}).to_list()
    return None

  async def _get_related_contests(self, pid):
    if self.has_perm(builtin.PERM_VIEW_CONTEST):
      return await contest.get_multi(self.domain_id, document.TYPE_CONTEST, pids=pid).to_list()
    return None

  async def _get_related_homework(self, pid):
    if self.has_perm(builtin.PERM_VIEW_HOMEWORK):
      return await contest.get_multi(self.domain_id, document.TYPE_HOMEWORK, pids=pid).to_list()
    return None

  @base.require_perm(builtin.PERM_VIEW_PROBLEM)
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    uid = self.user['_id'] if self.has_priv(builtin.PRIV_USER_PROFILE) else None
    pdoc = await problem.get(self.domain_id, pid, uid)
    if pdoc.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    udoc, dudoc = await asyncio.gather(user.get_by_uid(pdoc['owner_uid']),
                                       domain.get_user(self.domain_id, pdoc['owner_uid']))
    tdocs, ctdocs, htdocs = await asyncio.gather(self._get_related_trainings(pid),
                                                 self._get_related_contests(pid),
                                                 self._get_related_homework(pid))
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], None))
    self.render('problem_detail.html', pdoc=pdoc, udoc=udoc, dudoc=dudoc,
                tdocs=tdocs, ctdocs=ctdocs, htdocs=htdocs,
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
    udoc, dudoc = await asyncio.gather(user.get_by_uid(pdoc['owner_uid']),
                                       domain.get_user(self.domain_id, pdoc['owner_uid']))
    if uid == None:
      rdocs = []
    else:
      # TODO(iceboy): needs to be in sync with contest_detail_problem_submit
      rdocs = await record \
          .get_user_in_problem_multi(uid, self.domain_id, pdoc['doc_id']) \
          .sort([('_id', -1)]) \
          .limit(10) \
          .to_list()
    if not self.prefer_json:
      path_components = self.build_path(
          (self.translate('problem_main'), self.reverse_url('problem_main')),
          (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
          (self.translate('problem_submit'), None))
      self.render('problem_submit.html', pdoc=pdoc, udoc=udoc, rdocs=rdocs, dudoc=dudoc,
                  page_title=pdoc['title'], path_components=path_components)
    else:
      self.json({'rdocs': rdocs})

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_SUBMIT_PROBLEM)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  @base.limit_rate('add_record', 60, 100)
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str):
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
  @base.limit_rate('add_record', 60, 100)
  async def post(self, *, pid: document.convert_doc_id, lang: str, code: str,
                 data_input: str, data_output: str):
    pdoc = await problem.get(self.domain_id, pid)
    # don't need to check hidden status
    # create zip file, TODO(twd2): check file size
    post = await self.request.post()
    content = list(zip(post.getall('data_input'), post.getall('data_output')))
    output_buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(output_buffer, 'a', zipfile.ZIP_DEFLATED)
    config_content = str(len(content)) + '\n'
    for i, (data_input, data_output) in enumerate(content):
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
    fid = await fs.add_data('application/zip', output_buffer.getvalue())
    output_buffer.close()
    rid = await record.add(self.domain_id, pdoc['doc_id'], constant.record.TYPE_PRETEST,
                           self.user['_id'], lang, code, fid)
    self.json_or_redirect(self.reverse_url('record_detail', rid=rid))


@app.connection_route('/p/{pid}/pretest-conn', 'problem_pretest-conn')
class ProblemPretestConnection(record_handler.RecordVisibilityMixin, base.Connection):
  async def on_open(self):
    await super(ProblemPretestConnection, self).on_open()
    self.pid = document.convert_doc_id(self.request.match_info['pid'])
    bus.subscribe(self.on_record_change, ['record_change'])

  async def on_record_change(self, e):
    rdoc = e['value']
    if rdoc['uid'] != self.user['_id'] or \
       rdoc['domain_id'] != self.domain_id or rdoc['pid'] != self.pid:
      return
    # check permission for visibility: contest
    if rdoc['tid']:
      show_status, tdoc = await self.rdoc_contest_visible(rdoc)
      if not show_status:
        return
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
    await oplog.add(self.user['_id'], oplog.TYPE_DELETE_DOCUMENT, doc=psdoc)
    await problem.delete_solution(self.domain_id, psdoc['doc_id'])
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
      raise error.DocumentNotFoundError(self.domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
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
      raise error.DocumentNotFoundError(self.domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
    if not self.own(psrdoc, builtin.PERM_DELETE_PROBLEM_SOLUTION_REPLY_SELF):
      self.check_perm(builtin.PERM_DELETE_PROBLEM_SOLUTION_REPLY)
    await oplog.add(self.user['_id'], oplog.TYPE_DELETE_SUB_DOCUMENT, sub_doc=psrdoc,
                    doc_type=psdoc['doc_type'], doc_id=psdoc['doc_id'])
    await problem.delete_solution_reply(self.domain_id, psid, psrid)
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
      raise error.DocumentNotFoundError(self.domain_id, document.TYPE_PROBLEM_SOLUTION, psid)
    self.response.content_type = 'text/markdown'
    self.response.text = psrdoc['content']


@app.route('/p/{pid}/data', 'problem_data')
class ProblemDataHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, pid: document.convert_doc_id):
    # Judges will have PRIV_READ_PROBLEM_DATA,
    # domain administrators will have PERM_READ_PROBLEM_DATA,
    # problem owner will have PERM_READ_PROBLEM_DATA_SELF.
    pdoc = await problem.get(self.domain_id, pid)
    if (not self.own(pdoc, builtin.PERM_READ_PROBLEM_DATA_SELF)
        and not self.has_perm(builtin.PERM_READ_PROBLEM_DATA)):
      self.check_priv(builtin.PRIV_READ_PROBLEM_DATA)
    fdoc = await problem.get_data(self.domain_id, pid)
    if not fdoc:
      raise error.ProblemDataNotFoundError(self.domain_id, pid)
    self.redirect(options.cdn_prefix.rstrip('/') + \
                  self.reverse_url('fs_get', domain_id=builtin.DOMAIN_ID_SYSTEM,
                                   secret=fdoc['metadata']['secret']))


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
  async def post(self, *, title: str, content: str, hidden: bool=False, numeric_pid: bool=False):
    pid = None
    if numeric_pid:
      pid = await domain.inc_pid_counter(self.domain_id)
    pid = await problem.add(self.domain_id, title, content, self.user['_id'],
                            hidden=hidden, pid=pid)
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
    udoc, dudoc = await asyncio.gather(user.get_by_uid(pdoc['owner_uid']),
                                       domain.get_user(self.domain_id, pdoc['owner_uid']))
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_edit'), None))
    self.render('problem_edit.html', pdoc=pdoc, udoc=udoc, dudoc=dudoc,
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
    udoc, dudoc = await asyncio.gather(user.get_by_uid(pdoc['owner_uid']),
                                       domain.get_user(self.domain_id, pdoc['owner_uid']))
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_settings'), None))
    self.render('problem_settings.html', pdoc=pdoc, udoc=udoc, dudoc=dudoc,
                categories=problem.get_categories(),
                page_title=pdoc['title'], path_components=path_components)

  def split_tags(self, s):
    s = s.replace('，', ',') # Chinese ', '
    return list(filter(lambda _: _ != '', map(lambda _: _.strip(), s.split(','))))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, hidden: bool=False,
                 category: str, tag: str,
                 difficulty_setting: int, difficulty_admin: str=''):
    pdoc = await problem.get(self.domain_id, pid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    category = self.split_tags(category)
    tag = self.split_tags(tag)
    for c in category:
      if not (c in builtin.PROBLEM_CATEGORIES
              or c in builtin.PROBLEM_SUB_CATEGORIES):
        raise error.ValidationError('category')
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
                       category=category, tag=tag,
                       difficulty_setting=difficulty_setting, difficulty_admin=difficulty_admin)
    await job.difficulty.update_problem(self.domain_id, pdoc['doc_id'])
    self.json_or_redirect(self.reverse_url('problem_detail', pid=pid))


@app.route('/p/{pid}/upload', 'problem_upload')
class ProblemUploadHandler(base.Handler):
  def get_content_type(self, filename):
    if os.path.splitext(filename)[1].lower() != '.zip':
      raise error.FileTypeNotAllowedError(filename)
    return 'application/zip'

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
    md5 = await fs.get_md5(pdoc.get('data'))
    self.render('problem_upload.html', pdoc=pdoc, md5=md5)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.multipart_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, pid: document.convert_doc_id, file: objectid.ObjectId):
    pdoc = await problem.get(self.domain_id, pid)
    if not self.own(pdoc, builtin.PERM_EDIT_PROBLEM_SELF):
      self.check_perm(builtin.PERM_EDIT_PROBLEM)
    if (not self.own(pdoc, builtin.PERM_READ_PROBLEM_DATA_SELF)
        and not self.has_perm(builtin.PERM_READ_PROBLEM_DATA)):
      self.check_priv(builtin.PRIV_READ_PROBLEM_DATA)
    if pdoc.get('data'):
      await fs.unlink(pdoc['data'])
    await problem.set_data(self.domain_id, pid, file)
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
    udoc, dudoc = await asyncio.gather(user.get_by_uid(pdoc['owner_uid']),
                                       domain.get_user(self.domain_id, pdoc['owner_uid']))
    path_components = self.build_path(
        (self.translate('problem_main'), self.reverse_url('problem_main')),
        (pdoc['title'], self.reverse_url('problem_detail', pid=pdoc['doc_id'])),
        (self.translate('problem_statistics'), None))
    self.render('problem_statistics.html', pdoc=pdoc, udoc=udoc, dudoc=dudoc,
                page_title=pdoc['title'], path_components=path_components)


@app.route('/p/search', 'problem_search')
class ProblemSearchHandler(base.Handler):
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, q: str):
    q = q.strip()
    if not q:
      self.json_or_redirect(self.referer_or_main)
      return
    try:
      pdoc = await problem.get(self.domain_id, document.convert_doc_id(q))
    except error.ProblemNotFoundError:
      pdoc = None
    if pdoc:
      self.redirect(self.reverse_url('problem_detail', pid=pdoc['doc_id']))
      return
    self.redirect('http://cn.bing.com/search?q={0}+site%3A{1}' \
                  .format(parse.quote(q), parse.quote(options.url_prefix)))
