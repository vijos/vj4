import asyncio
import collections
import datetime
from bson import objectid
from pymongo import errors

from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.service import smallcache
from vj4.util import argmethod
from vj4.util import validator


ALLOWED_DOC_TYPES = [document.TYPE_PROBLEM, document.TYPE_PROBLEM_LIST,
                     document.TYPE_CONTEST, document.TYPE_TRAINING]


def node_id(ddoc):
  if ddoc['parent_doc_type'] == document.TYPE_DISCUSSION_NODE:
    return ddoc['parent_doc_id']
  else:
    return (ddoc['parent_doc_type'], ddoc['parent_doc_id'])


@argmethod.wrap
async def is_initialized(domain_id: str):
  doc = await document.get(domain_id, document.TYPE_DISCUSSION_NODE,
                           document.DOC_ID_DISCUSSION_NODES)
  return bool(doc)


@argmethod.wrap
async def initialize(domain_id: str):
  await _update_nodes(domain_id, builtin.DEFAULT_VNODES)


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
  validator.check_category_name(category_name)
  nodes = await get_nodes(domain_id)
  if category_name in nodes:
    raise error.DiscussionCategoryAlreadyExistError(domain_id, category_name)
  nodes[category_name] = []
  await _update_nodes(domain_id, nodes)


def _get_exist_node(nodes, node_name):
  for category in nodes.values():
    assert type(category) is list
    for node in category:
      if node['name'] == node_name:
        return node
  return None


@argmethod.wrap
async def add_node(domain_id: str, category_name: str, node_name: str, node_pic: str=None):
  validator.check_node_name(node_name)
  nodes = await get_nodes(domain_id)
  if category_name not in nodes:
    raise error.DiscussionCategoryNotFoundError(domain_id, category_name)
  if _get_exist_node(nodes, node_name):
    raise error.DiscussionNodeAlreadyExistError(domain_id, node_name)
  nodes[category_name].append({'name': node_name,
                               'pic': node_pic})
  await _update_nodes(domain_id, nodes)


@argmethod.wrap
async def get_exist_node(domain_id: str, node_name: str):
  nodes = await get_nodes(domain_id)
  return _get_exist_node(nodes, node_name)


@argmethod.wrap
async def delete_all_nodes(domain_id: str):
  await _update_nodes(domain_id, collections.OrderedDict())


async def check_node(domain_id, node_name):
  if not await get_exist_node(domain_id, node_name):
    raise error.DiscussionNodeNotFoundError(domain_id, node_name)


async def get_nodes_and_vnode(domain_id, node_or_dtuple):
  nodes = await get_nodes(domain_id)
  node = _get_exist_node(nodes, node_or_dtuple)
  if node:
    vnode = {'doc_id': node['name'],
            'doc_type': document.TYPE_DISCUSSION_NODE,
            'title': node['name'],
            'pic': node['pic']}
  elif isinstance(node_or_dtuple, tuple) and node_or_dtuple[0] in ALLOWED_DOC_TYPES:
    # TODO(twd2): projection.
    vnode = await document.get(domain_id, node_or_dtuple[0], node_or_dtuple[1])
  else:
    vnode = None
  return nodes, vnode


@argmethod.wrap
async def get_vnode(domain_id: str, node_or_dtuple: str):
  _, vnode = await get_nodes_and_vnode(domain_id, node_or_dtuple)
  return vnode


@argmethod.wrap
async def add(domain_id: str, node_or_dtuple: str, owner_uid: int, title: str, content: str,
              ip: str=None, **flags):
  validator.check_title(title)
  validator.check_content(content)
  vnode = await get_vnode(domain_id, node_or_dtuple)
  if not vnode:
      raise error.DiscussionNodeNotFoundError(domain_id, node_or_dtuple)
  return await document.add(domain_id, content, owner_uid, document.TYPE_DISCUSSION,
                            title=title, num_replies=0, views=0, ip=ip, **flags,
                            update_at=datetime.datetime.utcnow(),
                            parent_doc_type=vnode['doc_type'], parent_doc_id=vnode['doc_id'])


@argmethod.wrap
async def get(domain_id: str, did: document.convert_doc_id):
  return await document.get(domain_id, document.TYPE_DISCUSSION, did)


async def edit(domain_id: str, did: document.convert_doc_id, **kwargs):
  if 'title' in kwargs:
      validator.check_title(kwargs['title'])
  if 'content' in kwargs:
      validator.check_content(kwargs['content'])
  return await document.set(domain_id, document.TYPE_DISCUSSION, did, **kwargs)


@argmethod.wrap
async def delete(domain_id: str, did: document.convert_doc_id):
  # TODO(twd2): delete status?
  await document.delete(domain_id, document.TYPE_DISCUSSION, did)
  await document.delete_multi(domain_id, document.TYPE_DISCUSSION_REPLY,
                              parent_doc_type=document.TYPE_DISCUSSION,
                              parent_doc_id=did)


@argmethod.wrap
async def inc_views(domain_id: str, did: document.convert_doc_id):
  doc = await document.inc(domain_id, document.TYPE_DISCUSSION, did, 'views', 1)
  if not doc:
    raise error.DiscussionNotFoundError(domain_id, did)
  return doc


@argmethod.wrap
async def count(domain_id: str, **kwargs):
  return await document.get_multi(domain_id=domain_id, doc_type=document.TYPE_DISCUSSION,
                                  **kwargs).count()


@argmethod.wrap
def get_multi(domain_id: str, *, fields=None, **kwargs):
  return document.get_multi(domain_id=domain_id,
                            doc_type=document.TYPE_DISCUSSION,
                            fields=fields,
                            **kwargs) \
                 .sort([('update_at', -1),
                        ('doc_id', -1)])


@argmethod.wrap
async def add_reply(domain_id: str, did: document.convert_doc_id, owner_uid: int, content: str,
                    ip: str=None):
  validator.check_content(content)
  drdoc, _ = await asyncio.gather(
    document.add(domain_id, content, owner_uid, document.TYPE_DISCUSSION_REPLY, ip=ip,
                 parent_doc_type=document.TYPE_DISCUSSION, parent_doc_id=did),
    document.inc_and_set(domain_id, document.TYPE_DISCUSSION, did,
                         'num_replies', 1, 'update_at', datetime.datetime.utcnow()))
  return drdoc


@argmethod.wrap
async def get_reply(domain_id: str, drid: document.convert_doc_id, did=None):
  drdoc = await document.get(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
  if not drdoc or (did and drdoc['parent_doc_id'] != did):
    raise error.DocumentNotFoundError(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
  return drdoc


@argmethod.wrap
async def edit_reply(domain_id: str, drid: document.convert_doc_id, content: str):
  validator.check_content(content)
  drdoc = await document.set(domain_id, document.TYPE_DISCUSSION_REPLY, drid, content=content)
  return drdoc


@argmethod.wrap
async def delete_reply(domain_id: str, drid: document.convert_doc_id):
  drdoc = await get_reply(domain_id, drid)
  if not drdoc:
    return None
  await document.delete(domain_id, document.TYPE_DISCUSSION_REPLY, drid)
  await document.inc(domain_id, drdoc['parent_doc_type'], drdoc['parent_doc_id'],
                     'num_replies', -1)
  return drdoc


@argmethod.wrap
async def get_list_reply(domain_id: str, did: document.convert_doc_id, *, fields=None):
  return await document.get_multi(domain_id=domain_id,
                                  doc_type=document.TYPE_DISCUSSION_REPLY,
                                  parent_doc_type=document.TYPE_DISCUSSION,
                                  parent_doc_id=did,
                                  fields=fields) \
                       .sort([('doc_id', -1)]) \
                       .to_list(None)


def get_multi_reply(domain_id: str, did: document.convert_doc_id, *, fields=None):
  return document.get_multi(domain_id=domain_id,
                            doc_type=document.TYPE_DISCUSSION_REPLY,
                            parent_doc_type=document.TYPE_DISCUSSION,
                            parent_doc_id=did,
                            fields=fields) \
                 .sort([('doc_id', -1)])


@argmethod.wrap
async def add_tail_reply(domain_id: str, drid: document.convert_doc_id,
                         owner_uid: int, content: str, ip: str=None):
  validator.check_content(content)
  drdoc, sid = await document.push(domain_id, document.TYPE_DISCUSSION_REPLY, drid,
                                   'reply', content, owner_uid, ip=ip)
  await document.set(domain_id, document.TYPE_DISCUSSION, drdoc['parent_doc_id'],
                     update_at=datetime.datetime.utcnow())
  return drdoc, sid


@argmethod.wrap
def get_tail_reply(domain_id: str, drid: document.convert_doc_id, drrid: objectid.ObjectId):
  return document.get_sub(domain_id, document.TYPE_DISCUSSION_REPLY, drid, 'reply', drrid)


@argmethod.wrap
def edit_tail_reply(domain_id: str, drid: document.convert_doc_id, drrid: objectid.ObjectId,
                    content: str):
  return document.set_sub(domain_id, document.TYPE_DISCUSSION_REPLY, drid, 'reply', drrid,
                          content=content)


@argmethod.wrap
def delete_tail_reply(domain_id: str, drid: document.convert_doc_id, drrid: objectid.ObjectId):
  return document.delete_sub(domain_id, document.TYPE_DISCUSSION_REPLY, drid, 'reply', drrid)


async def get_dict_vnodes(domain_id, node_or_dtuples):
  nodes = await get_nodes(domain_id)
  result = dict()
  dtuples = set()
  for node_or_dtuple in node_or_dtuples:
    if _get_exist_node(nodes, node_or_dtuple):
      result[node_or_dtuple] = {'doc_id': node_or_dtuple,
                                'doc_type': document.TYPE_DISCUSSION_NODE,
                                'title': node_or_dtuple}
    elif node_or_dtuple[0] in ALLOWED_DOC_TYPES:
      dtuples.add(node_or_dtuple)
  for k, v in (await document.get_dict(domain_id=domain_id, dtuples=dtuples,
                                       fields=document.PROJECTION_PUBLIC)).items():
    result[k] = v
  return result


@argmethod.wrap
async def set_star(domain_id: str, did: document.convert_doc_id, uid: int, star: bool):
  return await document.set_status(domain_id, document.TYPE_DISCUSSION, did, uid, star=star)


@argmethod.wrap
async def get_status(domain_id: str, did: document.convert_doc_id, uid: int):
  return await document.get_status(domain_id, document.TYPE_DISCUSSION, did, uid)


if __name__ == '__main__':
  argmethod.invoke_by_args()
