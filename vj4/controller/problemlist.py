import itertools
from bson import objectid
from pymongo import errors
from vj4 import error
from vj4.model import document
from vj4.model import user
from vj4.util import argmethod

#创建提单(用户id，题单名称，提单描述)
#修改题单(题单id, 题单名称，题单描述)
#删除题单(题单id)
#添加题目到题单(题单id, 题目id)
#删除题单里的题目(题单id, 题目id)
#收藏题单(用户id, 题单id)
#取消收藏(用户id, 题单id)


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int,
              lid: document.convert_doc_id=None):
  return await document.add(domain_id, content, owner_uid,
                            document.TYPE_PROBLEM_LIST, lid, title=title)

@argmethod.wrap
async def get(domain_id: str, lid: document.convert_doc_id):
  return await document.get(domain_id, document.TYPE_PROBLEM_LIST, lid)

@argmethod.wrap
async def delete(domain_id: str, lid: document.convert_doc_id):
  return await document.set(domain_id, document.TYPE_PROBLEM_LIST, lid,
                            delete=True)

@argmethod.wrap
async def add_problem_to(domain_id: str, lid: document.convert_doc_id, pid: int):
  ldoc = await get(domain_id, lid)
  if not ldoc:
    return
  data = ldoc['data'] if 'data' in ldoc else []
  if pid not in data:
    data.append(pid)
  return await document.set(domain_id, document.TYPE_PROBLEM_LIST, lid,
                            data=data)

@argmethod.wrap
async def delete_problem_from(domain_id:str, lid: document.convert_doc_id, pid:int):
  ldoc = await get(domain_id, lid)
  if not ldoc:
    return
  data = ldoc['data'] if 'data' in ldoc else []
  if pid in data:
    data.remove(pid)
  return await document.set(domain_id, document.TYPE_PROBLEM_LIST, lid,
                            data=data)

@argmethod.wrap
async def star(domain_id: str, lid: document.convert_doc_id, uid: int):
  udoc = await user.get_by_uid(uid)
  if not udoc:
    return
  starlst = udoc['starlst'] if 'starlst' in udoc else []
  star = udoc['star'] if 'star' in udoc else 0
  if lid not in starlst:
    starlst.append(lid)
    star += 1
  return await user.set_by_uid(uid, starlst=starlst, star=star)

@argmethod.wrap
async def unstar():
  udoc = await user.get_by_uid(uid)
  if not udoc:
    return
  starlst = udoc['starlst'] if 'starlst' in udoc else []
  star = udoc['star'] if 'star' in udoc else 0
  if lid in starlst:
    starlst.remove(lid)
    star -= 1
  return await user.set_by_uid(uid, starlst=starlst, star=star)

if __name__ == '__main__':
  argmethod.invoke_by_args()
