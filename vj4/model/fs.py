import sys
import mimetypes

from bson import objectid
from pymongo import ReturnDocument

from vj4 import db
from vj4 import error
from vj4.util import argmethod
from vj4.util import pwhash


async def add(content_type):
  """Add a file. Returns MotorGridIn."""
  fs = db.fs('fs')
  secret = pwhash.gen_secret()
  return await fs.new_file(content_type=content_type,
                           metadata={'link': 1, 'secret': secret})


@argmethod.wrap
async def add_local(pathname: str, content_type: str=''):
  """Add a local file. Note: this method will block the thread."""
  with open(pathname, 'rb') as file_object:
    grid_in = await add(content_type or mimetypes.guess_type(pathname)[0])
    await grid_in.write(file_object)
    await grid_in.close()
    return grid_in._id


async def add_data(content_type, data):
  grid_in = await add(content_type)
  await grid_in.write(data)
  await grid_in.close()
  return grid_in._id


async def add_file_object(content_type, file_object):
  grid_in = await add(content_type)
  await grid_in.write(file_object)
  await grid_in.close()
  return grid_in._id


async def get(file_id):
  """Get a file. Returns MotorGridOut."""
  fs = db.fs('fs')
  return await fs.get(file_id)


async def get_by_secret(secret):
  """Get a file by secret. Returns MotorGridOut."""
  file_id = await get_file_id(str(secret))
  if file_id:
    return await get(file_id)
  else:
    raise error.NotFoundError(secret)


@argmethod.wrap
async def get_file_id(secret: str):
  """Get the _id of a file by secret."""
  coll = db.coll('fs.files')
  doc = await coll.find_one({'metadata.secret': secret})
  if doc:
    return doc['_id']


@argmethod.wrap
async def get_md5(file_id: objectid.ObjectId):
  """Get the MD5 checksum of a file."""
  coll = db.coll('fs.files')
  doc = await coll.find_one(file_id)
  if doc:
    return doc['md5']


@argmethod.wrap
async def get_datetime(file_id: objectid.ObjectId):
  """Get the upload date and time of a file."""
  coll = db.coll('fs.files')
  doc = await coll.find_one(file_id)
  if doc:
    return doc['uploadDate']


@argmethod.wrap
async def get_secret(file_id: objectid.ObjectId):
  """Get the secret of a file."""
  coll = db.coll('fs.files')
  doc = await coll.find_one(file_id)
  if doc:
    return doc['metadata']['secret']


@argmethod.wrap
async def get_meta(file_id: objectid.ObjectId):
  """Get all metadata of a file."""
  coll = db.coll('fs.files')
  doc = await coll.find_one(file_id)
  return doc


async def get_meta_dict(file_ids):
  result = dict()
  if not file_ids:
    return result
  coll = db.coll('fs.files')
  docs = coll.find({'_id': {'$in': list(set(file_ids))}})
  async for doc in docs:
    result[doc['_id']] = doc
  return result


@argmethod.wrap
async def cat(file_id: objectid.ObjectId):
  """Cat a file. Note: this method will block the thread."""
  grid_out = await get(file_id)
  buf = await grid_out.read()
  while buf:
    sys.stdout.buffer.write(buf)
    buf = await grid_out.read()


@argmethod.wrap
async def link_by_md5(file_md5: str, except_id: objectid.ObjectId=None):
  """Link a file by MD5 if exists."""
  query = {}
  if except_id:
    query['_id'] = {'$ne': except_id}
  coll = db.coll('fs.files')
  doc = await coll.find_one_and_update(filter={'md5': file_md5, **query},
                                       update={'$inc': {'metadata.link': 1}})
  if doc:
    return doc['_id']


@argmethod.wrap
async def unlink(file_id: objectid.ObjectId):
  """Unlink a file."""
  coll = db.coll('fs.files')
  doc = await coll.find_one_and_update(filter={'_id': file_id},
                                       update={'$inc': {'metadata.link': -1}},
                                       return_document=ReturnDocument.AFTER)
  if doc and not doc['metadata']['link']:
    fs = db.fs('fs')
    await fs.delete(file_id)


@argmethod.wrap
async def ensure_indexes():
  coll = db.coll('fs.files')
  await coll.create_index('metadata.secret', unique=True)
  await coll.create_index('md5')


if __name__ == '__main__':
  argmethod.invoke_by_args()
