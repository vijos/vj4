import asyncio
from bson import objectid
from pymongo import errors

from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import document
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
  await fs.unlink(doc['file_id'])
  return await document.delete(STORE_DOMAIN_ID, document.TYPE_USERFILE, fid)


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


if __name__ == '__main__':
  argmethod.invoke_by_args()
