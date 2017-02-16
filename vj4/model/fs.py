import sys

from bson import objectid
from pymongo import ReturnDocument

from vj4 import db
from vj4 import error
from vj4.util import argmethod
from vj4.util import pwhash


async def add():
  """Add a file. Returns MotorGridIn."""
  fs = db.GridFS('fs')
  secret = pwhash.gen_secret()
  return await fs.new_file(metadata={'link': 1, 'secret': secret})


@argmethod.wrap
async def add_local(pathname: str):
  """Add a local file. Note: this method will block the thread."""
  with open(pathname, 'rb') as file_object:
    grid_in = await add()
    await grid_in.write(file_object)
    await grid_in.close()
    return grid_in._id


async def add_data(data):
  grid_in = await add()
  await grid_in.write(data)
  await grid_in.close()
  return grid_in._id


async def get(file_id):
  """Get a file. Returns MotorGridOut."""
  fs = db.GridFS('fs')
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
  coll = db.Collection('fs.files')
  doc = await coll.find_one({'metadata.secret': secret})
  if doc:
    return doc['_id']


@argmethod.wrap
async def get_md5(file_id: objectid.ObjectId):
  """Get the MD5 checksum of a file."""
  coll = db.Collection('fs.files')
  doc = await coll.find_one(file_id)
  if doc:
    return doc['md5']


@argmethod.wrap
async def get_datetime(file_id: objectid.ObjectId):
  """Get the upload date and time of a file."""
  coll = db.Collection('fs.files')
  doc = await coll.find_one(file_id)
  if doc:
    return doc['uploadDate']


@argmethod.wrap
async def get_secret(file_id: objectid.ObjectId):
  """Get the secret of a file."""
  coll = db.Collection('fs.files')
  doc = await coll.find_one(file_id)
  if doc:
    return doc['metadata']['secret']


@argmethod.wrap
async def get_meta(file_id: objectid.ObjectId):
  """Get all metadata of a file."""
  coll = db.Collection('fs.files')
  doc = await coll.find_one(file_id)
  return doc


@argmethod.wrap
async def cat(file_id: objectid.ObjectId):
  """Cat a file. Note: this method will block the thread."""
  grid_out = await get(file_id)
  buf = await grid_out.read()
  while buf:
    sys.stdout.buffer.write(buf)
    buf = await grid_out.read()


@argmethod.wrap
async def link_by_md5(file_md5: str):
  """Link a file by MD5 if exists."""
  coll = db.Collection('fs.files')
  doc = await coll.find_one_and_update(filter={'md5': file_md5},
                                       update={'$inc': {'metadata.link': 1}})
  if doc:
    return doc['_id']


@argmethod.wrap
async def unlink(file_id: objectid.ObjectId):
  """Unlink a file."""
  coll = db.Collection('fs.files')
  doc = await coll.find_one_and_update(filter={'_id': file_id},
                                       update={'$inc': {'metadata.link': -1}},
                                       return_document=ReturnDocument.AFTER)
  if not doc['metadata']['link']:
    fs = db.GridFS('fs')
    await fs.delete(file_id)


@argmethod.wrap
async def ensure_indexes():
  coll = db.Collection('fs.files')
  await coll.create_index('metadata.secret', unique=True)


if __name__ == '__main__':
  argmethod.invoke_by_args()
