import asyncio

from vj4 import app
from vj4.model import builtin
from vj4.model import document
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.handler import base


@app.route('/discuss', 'discussion_main')
class DiscussionMainView(base.Handler):
  DISCUSSIONS_PER_PAGE = 15

  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.get_argument
  @base.sanitize
  async def get(self, *, page: int = 1):
    # TODO(iceboy): continuation based pagination.
    skip = (page - 1) * self.DISCUSSIONS_PER_PAGE
    limit = self.DISCUSSIONS_PER_PAGE
    nodes, ddocs, dcount = await asyncio.gather(discussion.get_nodes(self.domain_id),
                                                discussion.get_list(self.domain_id,
                                                                    skip=skip,
                                                                    limit=limit),
                                                discussion.count(self.domain_id))
    await asyncio.gather(user.attach_udocs(ddocs, 'owner_uid'),
                         attach_vnodes(ddocs, domain_id, 'parent_doc_id'))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, ddocs=ddocs,
                page=page, dcount=dcount)


@app.route('/discuss/{node_or_pid:\w{1,23}|\w{25,}|[^/]*[^/\w][^/]*}', 'discussion_node')
class DiscussionNodeView(base.Handler):
  DISCUSSIONS_PER_PAGE = 15

  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, node_or_pid: document.convert_doc_id, page: int = 1):
    # TODO(iceboy): continuation based pagination.
    nodes, (vnode, ddocs, dcount) = await asyncio.gather(
      discussion.get_nodes(self.domain_id),
      discussion.get_vnode_and_list_and_count_for_node(
        self.domain_id, node_or_pid,
        skip=(page - 1) * self.DISCUSSIONS_PER_PAGE, limit=self.DISCUSSIONS_PER_PAGE))
    await user.attach_udocs(ddocs, 'owner_uid')
    path_components = self.build_path(
      (self.translate('discussion_main'), self.reverse_url('discussion_main')),
      (vnode['title'], None))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, vnode=vnode,
                ddocs=ddocs, page=page, dcount=dcount, path_components=path_components)


@app.route('/discuss/{node_or_pid}/create', 'discussion_create')
class DiscussionCreateView(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, node_or_pid: document.convert_doc_id):
    vnode = await discussion.get_vnode(self.domain_id, node_or_pid, True)
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
  async def post(self, *, node_or_pid: document.convert_doc_id, title: str, content: str):
    did = await discussion.add(self.domain_id, node_or_pid, self.user['_id'], title, content)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did), did=did)


@app.route('/discuss/{did:\w{24}}', 'discussion_detail')
class DiscussionDetailView(base.OperationHandler):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  @base.sanitize
  async def get(self, *, did: document.convert_doc_id):
    ddoc = await discussion.inc_views(self.domain_id, did)
    udoc = await user.get_by_uid(ddoc['owner_uid'])
    vnode = await discussion.get_vnode(self.domain_id, ddoc['parent_doc_id'])
    path_components = self.build_path(
      (self.translate('discussion_main'), self.reverse_url('discussion_main')),
      (vnode['title'], self.reverse_url('discussion_node', node_or_pid=vnode['doc_id'])),
      (ddoc['title'], None))
    drdocs = await discussion.get_list_reply(self.domain_id, ddoc['doc_id'])
    drdocs_with_reply = list(drdocs)
    for drdoc in drdocs:
      if 'reply' in drdoc:
        drdocs_with_reply.extend(drdoc['reply'])
    await user.attach_udocs(drdocs_with_reply, 'owner_uid')
    self.render('discussion_detail.html', ddoc=ddoc, udoc=udoc, drdocs=drdocs, vnode=vnode,
                page_title=ddoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_REPLY_DISCUSSION)
  @base.route_argument
  @base.require_csrf_token
  @base.sanitize
  async def post_reply(self, *, did: document.convert_doc_id, content: str):
    ddoc = await discussion.get(self.domain_id, did)
    await discussion.add_reply(self.domain_id, ddoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_TAIL_REPLY_DISCUSSION)
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
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did))
