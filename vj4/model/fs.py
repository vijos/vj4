import sys

from bson import objectid
from pymongo import ReturnDocument

from vj4 import db
from vj4.util import argmethod


async def add():
  """Add a file. Returns MotorGridIn."""
  fs = db.GridFS('fs')
  return await fs.new_file(metadata={'link': 1})


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


if __name__ == '__main__':
  argmethod.invoke_by_args()
