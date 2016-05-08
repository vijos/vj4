import asyncio
import collections
from pymongo import errors
from vj4 import error
from vj4.controller import problem
from vj4.controller import smallcache
from vj4.model import document
from vj4.model import user
from vj4.util import argmethod

@argmethod.wrap
async def get_nodes(domain_id: str):
  items = smallcache.get_direct(smallcache.PREFIX_DISCUSSION_NODES + domain_id)
  if items is None:
    doc = await document.get(domain_id, document.TYPE_DISCUSSION_NODE,
                             document.DOC_ID_DISCUSSION_NODES)
    items = doc['content'] if doc else []
    smallcache.set_local_direct(smallcache.PREFIX_DISCUSSION_NODES + domain_id, items)
  return collections.OrderedDict(items)

async def _update_nodes(domain_id, nodes):
  items = list(nodes.items())
  try:
    await document.add(domain_id, items, 0, document.TYPE_DISCUSSION_NODE,
                       document.DOC_ID_DISCUSSION_NODES)
  except errors.DuplicateKeyError:
    doc = await document.set(domain_id, document.TYPE_DISCUSSION_NODE,
                             document.DOC_ID_DISCUSSION_NODES, content=items)
    if not doc:
      raise error.InvalidStateError()
  await smallcache.unset_global(smallcache.PREFIX_DISCUSSION_NODES + domain_id)

@argmethod.wrap
async def add_category(domain_id: str, category_name: str):
  nodes = await get_nodes(domain_id)
  if category_name in nodes:
    raise error.DiscussionCategoryAlreadyExistError(domain_id, category_name)
  nodes[category_name] = []
  await _update_nodes(domain_id, nodes)

def _is_exist_node(nodes, node_name):
  for category in nodes.values():
    assert type(category) is list
    if node_name in category:
      return True
  return False

@argmethod.wrap
async def add_node(domain_id: str, category_name: str, node_name: str):
  nodes = await get_nodes(domain_id)
  if category_name not in nodes:
    raise error.DiscussionCategoryNotFoundError(domain_id, category_name)
  if _is_exist_node(nodes, node_name):
    raise error.DiscussionNodeAlreadyExistError(domain_id, node_name)
  nodes[category_name].append(node_name)
  await _update_nodes(domain_id, nodes)

@argmethod.wrap
async def is_exist_node(domain_id: str, node_name: str):
  nodes = await get_nodes(domain_id)
  return _is_exist_node(nodes, node_name)

@argmethod.wrap
async def delete_all_nodes(domain_id: str):
  await _update_nodes(domain_id, collections.OrderedDict())

async def check_node(domain_id, node_name):
  if not await is_exist_node(domain_id, node_name):
    raise error.DiscussionNodeNotFoundError(domain_id, node_name)

@argmethod.wrap
async def get_vnode(domain_id: str, node_or_pid: document.convert_doc_id):
  if await is_exist_node(domain_id, node_or_pid):
    return {'doc_id': node_or_pid, 'doc_type': document.TYPE_DISCUSSION_NODE, 'title': node_or_pid}
  else:
    return await problem.get(domain_id, node_or_pid)

@argmethod.wrap
async def add(domain_id: str, node_or_pid: str, owner_uid: int, title: str, content: str):
  vnode = await get_vnode(domain_id, node_or_pid)
  return await document.add(domain_id, content, owner_uid, document.TYPE_DISCUSSION, title=title,
                            parent_doc_type=vnode['doc_type'],
                            parent_doc_id=vnode['doc_id'])

@argmethod.wrap
async def get(domain_id: str, did: document.convert_doc_id):
  return await document.get(domain_id, document.TYPE_DISCUSSION, did)

@argmethod.wrap
async def inc_views(domain_id: str, did: document.convert_doc_id):
  return await document.inc(domain_id, document.TYPE_DISCUSSION, did, 'views', 1)

@argmethod.wrap
async def get_list(domain_id: str, *, fields=None):
  # TODO(iceboy): projection, pagination.
  ddocs = await (document.get_multi(domain_id, document.TYPE_DISCUSSION, fields=fields)
                         .sort([('doc_id', -1)])
                         .to_list(None))
  await asyncio.gather(user.attach_udocs(ddocs, 'owner_uid'),
                       attach_vnodes(ddocs, domain_id, 'parent_doc_id'))
  return ddocs

@argmethod.wrap
async def get_vnode_and_list_for_node(domain_id: str, node_or_pid: document.convert_doc_id, *,
                                      fields=None):
  vnode = await get_vnode(domain_id, node_or_pid)
  # TODO(iceboy): projection, pagination.
  ddocs = await (document.get_multi(domain_id, document.TYPE_DISCUSSION,
                                    parent_doc_type=vnode['doc_type'],
                                    parent_doc_id=vnode['doc_id'],
                                    fields=fields)
                         .sort([('doc_id', -1)])
                         .to_list(None))
  await asyncio.gather(user.attach_udocs(ddocs, 'owner_uid'),
                       attach_vnodes(ddocs, domain_id, 'parent_doc_id'))
  return vnode, ddocs

@argmethod.wrap
async def get_list_for_node(domain_id: str, node_or_pid: document.convert_doc_id, *, fields=None):
  _, ddocs = await get_vnode_and_list_for_node(domain_id, node_or_pid, fields=fields)
  return ddocs

@argmethod.wrap
async def add_reply(domain_id: str, did: document.convert_doc_id, owner_uid: int, content: str):
  return await document.add(domain_id, content, owner_uid, document.TYPE_DISCUSSION_REPLY,
                            parent_doc_type=document.TYPE_DISCUSSION, parent_doc_id=did)

@argmethod.wrap
async def get_reply(domain_id: str, drid: document.convert_doc_id, did=None):
  drdoc = await document.get(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
  if not drdoc or (did and drdoc['parent_doc_id'] != did):
    raise error.DocumentNotFoundError(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
  return drdoc

@argmethod.wrap
async def get_list_reply(domain_id: str, did: document.convert_doc_id, *, fields=None):
  drdocs = await (document.get_multi(domain_id, document.TYPE_DISCUSSION_REPLY,
                                     parent_doc_type=document.TYPE_DISCUSSION, parent_doc_id=did,
                                     fields=fields)
                          .sort([('doc_id', -1)])
                          .to_list(None))
  drdocs_with_reply = list(drdocs)
  for drdoc in drdocs:
    if 'reply' in drdoc:
      drdocs_with_reply.extend(drdoc['reply'])
  await user.attach_udocs(drdocs_with_reply, 'owner_uid')
  return drdocs

@argmethod.wrap
async def add_tail_reply(domain_id: str, drid: document.convert_doc_id,
                         owner_uid: int, content: str):
  return await document.push(domain_id, document.TYPE_DISCUSSION_REPLY, drid,
                             'reply', content, owner_uid)

async def attach_vnodes(docs, domain_id, field_name):
  # TODO(iceboy): projection.
  nodes = await get_nodes(domain_id)
  pids = set(doc[field_name] for doc in docs if not _is_exist_node(nodes, doc[field_name]))
  pdocs = await document.get_multi(domain_id, document.TYPE_PROBLEM,
                                   doc_id={'$in': list(pids)}).to_list(None)
  pids = dict((pdoc['doc_id'], pdoc) for pdoc in pdocs)
  for doc in docs:
    if _is_exist_node(nodes, doc[field_name]):
      doc['vnode'] = {'doc_id': doc[field_name],
                      'doc_type': document.TYPE_DISCUSSION_NODE,
                      'title': doc[field_name]}
    else:
      doc['vnode'] = pids.get(doc[field_name])

if __name__ == '__main__':
  argmethod.invoke_by_args()
