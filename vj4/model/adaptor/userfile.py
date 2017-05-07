from bson import objectid

from vj4 import error
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model import fs
from vj4.util import argmethod
from vj4.util import validator


STORE_DOMAIN_ID = builtin.DOMAIN_ID_SYSTEM


@argmethod.wrap
async def add(desc: str, file_id: objectid.ObjectId, owner_uid: int, length: int):
  validator.check_title(desc)
  return await document.add(STORE_DOMAIN_ID, desc, owner_uid, document.TYPE_USERFILE,
                            file_id=file_id, length=length)


@argmethod.wrap
async def get(fid: objectid.ObjectId):
  doc = await document.get(STORE_DOMAIN_ID, document.TYPE_USERFILE, fid)
  if not doc:
    raise error.DocumentNotFoundError(STORE_DOMAIN_ID, document.TYPE_USERFILE, fid)
  return doc


@argmethod.wrap
async def delete(fid: objectid.ObjectId):
  doc = await get(fid)
  result = await document.delete(STORE_DOMAIN_ID, document.TYPE_USERFILE, fid)
  result = bool(result.deleted_count)
  if result:
    await fs.unlink(doc['file_id'])
  return result


def get_multi(fields=None, **kwargs):
  return document.get_multi(domain_id=STORE_DOMAIN_ID, doc_type=document.TYPE_USERFILE,
                            fields=fields, **kwargs)


async def get_dict(fids, *, fields=None):
  result = dict()
  if not fids:
    return result
  async for doc in get_multi(doc_id={'$in': list(set(fids))},
                             fields=fields):
    result[doc['doc_id']] = doc
  return result


@argmethod.wrap
async def get_usage(uid: int):
  dudoc = await domain.get_user(STORE_DOMAIN_ID, uid)
  if not dudoc:
    return 0
  return dudoc.get('usage_userfile', 0)


@argmethod.wrap
async def inc_usage(uid: int, usage: int, quota: int):
  return await domain.inc_user_usage(STORE_DOMAIN_ID, uid, 'usage_userfile', usage, quota)


@argmethod.wrap
async def dec_usage(uid: int, usage: int):
  return await domain.inc_user(STORE_DOMAIN_ID, uid, usage_userfile=-usage)


if __name__ == '__main__':
  argmethod.invoke_by_args()
