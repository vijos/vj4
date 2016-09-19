import asyncio
import functools
from bson import objectid

from vj4 import app
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.handler import base
from vj4.util import pagination


@app.route('/discuss', 'discussion_main')
class DiscussionMainHandler(base.Handler):
  DISCUSSIONS_PER_PAGE = 15

  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.get_argument
  @base.sanitize
  async def get(self, *, page: int=1):
    # TODO(iceboy): continuation based pagination.
    nodes, (ddocs, dpcount, _) = await asyncio.gather(
        discussion.get_nodes(self.domain_id),
        pagination.paginate(discussion.get_multi(self.domain_id), page, self.DISCUSSIONS_PER_PAGE))
    udict, vndict = await asyncio.gather(
        user.get_dict(ddoc['owner_uid'] for ddoc in ddocs),
        discussion.get_dict_vnodes(self.domain_id, (ddoc['parent_doc_id'] for ddoc in ddocs)))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, ddocs=ddocs,
                udict=udict, vndict=vndict, page=page, dpcount=dpcount)


@app.route('/discuss/{node_or_pid:\w{1,23}|\w{25,}|[^/]*[^/\w][^/]*}', 'discussion_node')
class DiscussionNodeHandler(base.Handler):
  DISCUSSIONS_PER_PAGE = 15

  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, node_or_pid: document.convert_doc_id, page: int=1):
    nodes, vnode = await discussion.get_nodes_and_vnode(self.domain_id, node_or_pid)
    # TODO(iceboy): continuation based pagination.
    ddocs, dpcount, _ = await pagination.paginate(discussion.get_multi(self.domain_id),
                                                  page, self.DISCUSSIONS_PER_PAGE)
    udict, vndict = await asyncio.gather(
        user.get_dict(ddoc['owner_uid'] for ddoc in ddocs),
        discussion.get_dict_vnodes(self.domain_id, (ddoc['parent_doc_id'] for ddoc in ddocs)))
    path_components = self.build_path(
        (self.translate('discussion_main'), self.reverse_url('discussion_main')),
        (vnode['title'], None))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, vnode=vnode, ddocs=ddocs,
                udict=udict, vndict=vndict, page=page, dpcount=dpcount,
                path_components=path_components)


@app.route('/discuss/{node_or_pid}/create', 'discussion_create')
class DiscussionCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, node_or_pid: document.convert_doc_id):
    vnode = await discussion.get_vnode(self.domain_id, node_or_pid)
    path_components = self.build_path(
        (self.translate('discussion_main'), self.reverse_url('discussion_main')),
        (vnode['title'], self.reverse_url('discussion_node', node_or_pid=vnode['doc_id'])),
        (self.translate('discussion_create'), None))
    self.render('discussion_create.html', vnode=vnode, path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, node_or_pid: document.convert_doc_id, title: str, content: str,
                 highlight: str=None):
    flags = {}
    if highlight:
      self.check_perm(builtin.PERM_HIGHLIGHT_DISCUSSION)
      flags['highlight'] = True
    did = await discussion.add(self.domain_id, node_or_pid, self.user['_id'], title, content,
                               **flags)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did), did=did)


@app.route('/discuss/{did:\w{24}}', 'discussion_detail')
class DiscussionDetailHandler(base.OperationHandler):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id):
    ddoc = await discussion.inc_views(self.domain_id, did)
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      dsdoc = await discussion.get_status(self.domain_id, ddoc['doc_id'], self.user['_id'])
    else:
      dsdoc = None
    vnode, drdocs = await asyncio.gather(
        discussion.get_vnode(self.domain_id, ddoc['parent_doc_id']),
        discussion.get_list_reply(self.domain_id, ddoc['doc_id']))
    uids = {ddoc['owner_uid']}
    uids.update(drdoc['owner_uid'] for drdoc in drdocs)
    for drdoc in drdocs:
      if 'reply' in drdoc:
        uids.update(drrdoc['owner_uid'] for drrdoc in drdoc['reply'])
    udict, dudict = await asyncio.gather(user.get_dict(uids),
                                         domain.get_dict_user_by_uid(self.domain_id, uids))
    path_components = self.build_path(
        (self.translate('discussion_main'), self.reverse_url('discussion_main')),
        (vnode['title'], self.reverse_url('discussion_node', node_or_pid=vnode['doc_id'])),
        (ddoc['title'], None))
    self.render('discussion_detail.html', page_title=ddoc['title'], path_components=path_components,
                ddoc=ddoc, dsdoc=dsdoc, drdocs=drdocs, vnode=vnode, udict=udict, dudict=dudict)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_REPLY_DISCUSSION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_reply(self, *, did: document.convert_doc_id, content: str):
    ddoc = await discussion.get(self.domain_id, did)
    await discussion.add_reply(self.domain_id, ddoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_REPLY_DISCUSSION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_tail_reply(self, *,
                            did: document.convert_doc_id,
                            drid: document.convert_doc_id,
                            content: str):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc = await discussion.get_reply(self.domain_id, drid, ddoc['doc_id'])
    await discussion.add_tail_reply(self.domain_id, drdoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_edit_reply(self, *, did: document.convert_doc_id,
                            drid: document.convert_doc_id, content: str):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc = await discussion.get_reply(self.domain_id, drid, ddoc['doc_id'])
    if (not self.own(ddoc, builtin.PERM_EDIT_DISCUSSION_REPLY_SELF_DISCUSSION)
        and not self.own(drdoc, builtin.PERM_EDIT_DISCUSSION_REPLY_SELF)):
      self.check_perm(builtin.PERM_EDIT_DISCUSSION_REPLY)
    drdoc = await discussion.edit_reply(self.domain_id, drdoc['doc_id'],
                                        content=content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_reply(self, *, did: document.convert_doc_id,
                              drid: document.convert_doc_id):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc = await discussion.get_reply(self.domain_id, drid, ddoc['doc_id'])
    if (not self.own(ddoc, builtin.PERM_DELETE_DISCUSSION_REPLY_SELF_DISCUSSION)
        and not self.own(drdoc, builtin.PERM_DELETE_DISCUSSION_REPLY_SELF)):
      self.check_perm(builtin.PERM_DELETE_DISCUSSION_REPLY)
    drdoc = await discussion.delete_reply(self.domain_id, drdoc['doc_id'])
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_edit_tail_reply(self, *, did: document.convert_doc_id,
                                 drid: document.convert_doc_id, drrid: document.convert_doc_id,
                                 content: str):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc, drrdoc = await discussion.get_tail_reply(self.domain_id, drid, drrid)
    if not drdoc or drdoc['parent_doc_id'] != ddoc['doc_id']:
      raise error.DocumentNotFoundError(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
    if (not self.own(ddoc, builtin.PERM_EDIT_DISCUSSION_REPLY_SELF_DISCUSSION)
        and not self.own(drrdoc, builtin.PERM_EDIT_DISCUSSION_REPLY_SELF)):
      self.check_perm(builtin.PERM_EDIT_DISCUSSION_REPLY)
    await discussion.edit_tail_reply(self.domain_id, drid, drrid, content)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_delete_tail_reply(self, *, did: document.convert_doc_id,
                                   drid: document.convert_doc_id, drrid: objectid.ObjectId):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc, drrdoc = await discussion.get_tail_reply(self.domain_id, drid, drrid)
    if not drdoc or drdoc['parent_doc_id'] != ddoc['doc_id']:
      raise error.DocumentNotFoundError(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
    if (not self.own(ddoc, builtin.PERM_DELETE_DISCUSSION_REPLY_SELF_DISCUSSION)
        and not self.own(drrdoc, builtin.PERM_DELETE_DISCUSSION_REPLY_SELF)):
      self.check_perm(builtin.PERM_DELETE_DISCUSSION_REPLY)
    await discussion.delete_tail_reply(self.domain_id, drid, drrid)
    self.json_or_redirect(self.url)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def star_unstar(self, *, did: document.convert_doc_id, star: bool):
    ddoc = await discussion.get(self.domain_id, did)
    ddoc = await discussion.set_star(self.domain_id, ddoc['doc_id'], self.user['_id'], star)
    self.json_or_redirect(self.url, star=ddoc['star'])

  post_star = functools.partialmethod(star_unstar, star=True)
  post_unstar = functools.partialmethod(star_unstar, star=False)


@app.route('/discuss/{did:\w{24}}/raw', 'discussion_detail_raw')
class DiscussionDetailRawHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id):
    ddoc = await discussion.get(self.domain_id, did)
    self.response.content_type = 'text/markdown'
    self.response.text = ddoc['content']


@app.route('/discuss/{did:\w{24}}/{drid:\w{24}}/raw', 'discussion_reply_raw')
class DiscussionReplyRawHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id, drid: document.convert_doc_id):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc = await discussion.get_reply(self.domain_id, drid, ddoc['doc_id'])
    self.response.content_type = 'text/markdown'
    self.response.text = drdoc['content']


@app.route('/discuss/{did:\w{24}}/{drid:\w{24}}/{drrid:\w{24}}/raw', 'discussion_tail_reply_raw')
class DiscussionTailReplyRawHandler(base.Handler):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id, drid: document.convert_doc_id,
                drrid: objectid.ObjectId):
    ddoc = await discussion.get(self.domain_id, did)
    drdoc, drrdoc = await discussion.get_tail_reply(self.domain_id, drid, drrid)
    self.response.content_type = 'text/markdown'
    self.response.text = drrdoc['content']
