import asyncio
from vj4 import app
from vj4.controller import discussion
from vj4.model import builtin
from vj4.model import document
from vj4.model import user
from vj4.view import base

@app.route('/discuss', 'discussion_main')
class DiscussionMainView(base.View):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  async def get(self):
    nodes, ddocs = await asyncio.gather(discussion.get_nodes(self.domain_id),
                                        discussion.get_list(self.domain_id))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, ddocs=ddocs)

@app.route('/discuss/{node_or_pid:\w{1,23}|\w{25,}|[^/]*[^/\w][^/]*}', 'discussion_node')
class DiscussionMainView(base.View):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  async def get(self, *, node_or_pid):
    nodes, (vnode, ddocs) = await asyncio.gather(
        discussion.get_nodes(self.domain_id),
        discussion.get_vnode_and_list_for_node(self.domain_id,
                                               document.convert_doc_id(node_or_pid)))
    path_components = self.build_path(('discussion_main', self.reverse_url('discussion_main')),
                                      (vnode['title'], None))
    self.render('discussion_main_or_node.html', discussion_nodes=nodes, vnode=vnode, ddocs=ddocs,
                path_components=path_components)

@app.route('/discuss/{node_or_pid}/create', 'discussion_create')
class DiscussionCreateView(base.View):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  async def get(self, *, node_or_pid):
    vnode = await discussion.get_vnode(self.domain_id, document.convert_doc_id(node_or_pid))
    path_components = self.build_path(
        ('discussion_main', self.reverse_url('discussion_main')),
        (vnode['title'], self.reverse_url('discussion_node', node_or_pid=vnode['doc_id'])),
        ('discussion_create', None))
    self.render('discussion_create.html', vnode=vnode, path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_CREATE_DISCUSSION)
  @base.route_argument
  @base.post_argument
  @base.require_csrf_token
  async def post(self, *, node_or_pid, title, content):
    did = await discussion.add(self.domain_id, document.convert_doc_id(node_or_pid),
                               self.user['_id'], title, content)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did), did=did)

@app.route('/discuss/{did:\w{24}}', 'discussion_detail')
class DiscussionDetailView(base.OperationView):
  @base.require_perm(builtin.PERM_VIEW_DISCUSSION)
  @base.route_argument
  async def get(self, *, did):
    ddoc = await discussion.inc_views(self.domain_id, document.convert_doc_id(did))
    udoc = await user.get_by_uid(ddoc['owner_uid'])
    vnode = await discussion.get_vnode(self.domain_id, ddoc['parent_doc_id'])
    path_components = self.build_path(
        ('discussion_main', self.reverse_url('discussion_main')),
        (vnode['title'], self.reverse_url('discussion_node', node_or_pid=vnode['doc_id'])),
        (ddoc['title'], None))
    drdocs = await discussion.get_list_reply(self.domain_id, ddoc['doc_id'])
    self.render('discussion_detail.html', ddoc=ddoc, udoc=udoc, drdocs=drdocs, vnode=vnode,
                page_title=ddoc['title'], path_components=path_components)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_REPLY_DISCUSSION)
  @base.route_argument
  @base.require_csrf_token
  async def post_reply(self, *, did, content):
    ddoc = await discussion.get(self.domain_id, document.convert_doc_id(did))
    await discussion.add_reply(self.domain_id, ddoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did))

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_TAIL_REPLY_DISCUSSION)
  @base.route_argument
  @base.require_csrf_token
  async def post_tail_reply(self, *, did, drid, content):
    ddoc = await discussion.get(self.domain_id, document.convert_doc_id(did))
    drdoc = await discussion.get_reply(self.domain_id,
                                       document.convert_doc_id(drid),
                                       ddoc['doc_id'])
    await discussion.add_tail_reply(self.domain_id, drdoc['doc_id'], self.user['_id'], content)
    self.json_or_redirect(self.reverse_url('discussion_detail', did=did))
