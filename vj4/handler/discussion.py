import asyncio
import functools
from bson import objectid

from vj4 import app
from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import oplog
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.handler import base
from vj4.handler import contest as contest_handler
from vj4.util import pagination


def node_url(handler, name, node_or_dtuple):
  if isinstance(node_or_dtuple, tuple):
    name += '_document_as_node'
    kwargs = {'doc_type': node_or_dtuple[0], 'doc_id': node_or_dtuple[1]}
  else:
    kwargs = {'doc_id': node_or_dtuple}
  return handler.reverse_url(name, **kwargs)


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
        # TODO(twd2): exclude problem/contest discussions?
        pagination.paginate(discussion.get_multi(self.domain_id), page, self.DISCUSSIONS_PER_PAGE))
    udict, vndict = await asyncio.gather(
        user.get_dict(ddoc['owner_uid'] for ddoc in ddocs),
        discussion.get_dict_vnodes(self.domain_id, map(discussion.node_id, ddocs)))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, ddocs=ddocs,
                udict=udict, vndict=vndict, page=page, dpcount=dpcount)


@app.route('/discuss/{doc_type:-?\d+}/{doc_id}', 'discussion_node_document_as_node')
@app.route('/discuss/{doc_id:\w{1,23}|\w{25,}|[^/]*[^/\w][^/]*}', 'discussion_node')
class DiscussionNodeHandler(contest_handler.ContestStatusMixin, base.Handler):
  DISCUSSIONS_PER_PAGE = 15

  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, doc_type: int=None, doc_id: str, page: int=1):
    if doc_type is None:
      node_or_dtuple = doc_id
    else:
      node_or_dtuple = (doc_type, document.convert_doc_id(doc_id))
    nodes, vnode = await discussion.get_nodes_and_vnode(self.domain_id, node_or_dtuple)
    if not vnode:
      raise error.DiscussionNodeNotFoundError(self.domain_id, node_or_dtuple)
    if vnode['doc_type'] == document.TYPE_PROBLEM and vnode.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    # TODO(twd2): do more visibility check eg. contest
    # TODO(iceboy): continuation based pagination.
    ddocs, dpcount, _ = await pagination.paginate(
        discussion.get_multi(self.domain_id,
                             parent_doc_type=vnode['doc_type'],
                             parent_doc_id=vnode['doc_id']),
        page, self.DISCUSSIONS_PER_PAGE)
    uids = set(ddoc['owner_uid'] for ddoc in ddocs)
    if 'owner_uid' in vnode:
      uids.add(vnode['owner_uid'])
    udict = await user.get_dict(uids)
    vndict = {node_or_dtuple: vnode}
    vncontext = {} # TODO(twd2): eg. psdoc, tsdoc, ...
    path_components = self.build_path(
        (self.translate('discussion_main'), self.reverse_url('discussion_main')),
        (vnode['title'], None))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, vnode=vnode, ddocs=ddocs,
                udict=udict, vndict=vndict, page=page, dpcount=dpcount, **vncontext,
                path_components=path_components)


@app.route('/discuss/{doc_type:-?\d+}/{doc_id}/create', 'discussion_create_document_as_node')
@app.route('/discuss/{doc_id}/create', 'discussion_create')
class DiscussionCreateHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, doc_type: int=None, doc_id: str):
    if doc_type is None:
      node_or_dtuple = doc_id
    else:
      node_or_dtuple = (doc_type, document.convert_doc_id(doc_id))
    nodes, vnode = await discussion.get_nodes_and_vnode(self.domain_id, node_or_dtuple)
    if not vnode:
      raise error.DiscussionNodeNotFoundError(self.domain_id, node_or_dtuple)
    if vnode['doc_type'] == document.TYPE_PROBLEM and vnode.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    # TODO(twd2): do more visibility check eg. contest
    path_components = self.build_path(
        (self.translate('discussion_main'), self.reverse_url('discussion_main')),
        (vnode['title'], node_url(self, 'discussion_node', node_or_dtuple)),
        (self.translate('discussion_create'), None))
    self.render('discussion_create.html', vnode=vnode, path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, doc_type: int=None, doc_id: str, title: str, content: str,
                 highlight: str=None):
    if doc_type is None:
      node_or_dtuple = doc_id
    else:
      node_or_dtuple = (doc_type, document.convert_doc_id(doc_id))
    vnode = await discussion.get_vnode(self.domain_id, node_or_dtuple)
    if not vnode:
      raise error.DiscussionNodeNotFoundError(self.domain_id, node_or_dtuple)
    if vnode['doc_type'] == document.TYPE_PROBLEM and vnode.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    # TODO(twd2): do more visibility check eg. contest
    flags = {}
    if highlight:
      self.check_perm(builtin.PERM_HIGHLIGHT_DISCUSSION)
      flags['highlight'] = True
    did = await discussion.add(self.domain_id, node_or_dtuple, self.user['_id'], title, content,
                               **flags)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did), did=did)


@app.route('/discuss/{did:\w{24}}', 'discussion_detail')
class DiscussionDetailHandler(base.OperationHandler):
  REPLIES_PER_PAGE = 50

  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id, page: int=1):
    ddoc = await discussion.inc_views(self.domain_id, did)
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      dsdoc = await discussion.get_status(self.domain_id, ddoc['doc_id'], self.user['_id'])
    else:
      dsdoc = None
    vnode, (drdocs, pcount, drcount) = await asyncio.gather(
        discussion.get_vnode(self.domain_id, discussion.node_id(ddoc)),
        pagination.paginate(discussion.get_multi_reply(self.domain_id, ddoc['doc_id']),
                            page, self.REPLIES_PER_PAGE))
    if not vnode:
      vnode = builtin.VNODE_MISSING
    elif vnode['doc_type'] == document.TYPE_PROBLEM and vnode.get('hidden', False):
      self.check_perm(builtin.PERM_VIEW_PROBLEM_HIDDEN)
    # TODO(twd2): do more visibility check eg. contest
    uids = {ddoc['owner_uid']}
    uids.update(drdoc['owner_uid'] for drdoc in drdocs)
    for drdoc in drdocs:
      if 'reply' in drdoc:
        uids.update(drrdoc['owner_uid'] for drrdoc in drdoc['reply'])
    if 'owner_uid' in vnode:
      uids.add(vnode['owner_uid'])
    udict, dudict = await asyncio.gather(user.get_dict(uids),
                                         domain.get_dict_user_by_uid(self.domain_id, uids))
    path_components = self.build_path(
        (self.translate('discussion_main'), self.reverse_url('discussion_main')),
        (vnode['title'], node_url(self, 'discussion_node', discussion.node_id(ddoc))),
        (ddoc['title'], None))
    self.render('discussion_detail.html', page_title=ddoc['title'], path_components=path_components,
                ddoc=ddoc, dsdoc=dsdoc, drdocs=drdocs, page=page, pcount=pcount, drcount=drcount,
                vnode=vnode, udict=udict, dudict=dudict)

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
    await oplog.add(self.user['_id'], oplog.TYPE_DELETE_DOCUMENT, doc=drdoc)
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
    await oplog.add(self.user['_id'], oplog.TYPE_DELETE_SUB_DOCUMENT, sub_doc=drrdoc,
                    doc_type=drdoc['doc_type'], doc_id=drdoc['doc_id'])
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


@app.route('/discuss/{did:\w{24}}/edit', 'discussion_edit')
class DiscussionEditHandler(base.OperationHandler):
  DEFAULT_OPERATION = 'update'

  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id):
    ddoc = await discussion.get(self.domain_id, did)
    if not ddoc:
      raise error.DiscussionNotFoundError(self.domain_id, did)
    if not self.own(ddoc, builtin.PERM_EDIT_DISCUSSION_SELF):
      self.check_perm(builtin.PERM_EDIT_DISCUSSION)
    self.render('discussion_edit.html', ddoc=ddoc)

  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_update(self, *, did: document.convert_doc_id, title: str, content: str,
                        highlight: str=None):
    ddoc = await discussion.get(self.domain_id, did)
    if not ddoc:
      raise error.DiscussionNotFoundError(self.domain_id, did)
    if not self.own(ddoc, builtin.PERM_EDIT_DISCUSSION_SELF):
      self.check_perm(builtin.PERM_EDIT_DISCUSSION)
    flags = {}
    if highlight:
      if not ddoc.get('highlight'):
        self.check_perm(builtin.PERM_HIGHLIGHT_DISCUSSION)
      flags['highlight'] = True
    else:
      flags['highlight'] = False
    ddoc = await discussion.edit(self.domain_id, did, title=title, content=content, **flags)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=ddoc['doc_id']))

  @base.route_argument
  @base.require_csrf_token
  async def post_delete(self, *, did: document.convert_doc_id, **kwargs):
    did = document.convert_doc_id(did)
    ddoc = await discussion.get(self.domain_id, did)
    if not ddoc:
      raise error.DiscussionNotFoundError(self.domain_id, did)
    if not self.own(ddoc, builtin.PERM_DELETE_DISCUSSION_SELF):
      self.check_perm(builtin.PERM_DELETE_DISCUSSION)
    await oplog.add(self.user['_id'], oplog.TYPE_DELETE_DOCUMENT, doc=ddoc)
    await discussion.delete(self.domain_id, did)
    self.json_or_redirect(node_url(self, 'discussion_node', discussion.node_id(ddoc)))
