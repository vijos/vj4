import asyncio
import collections
import functools
import hashlib
import mimetypes
from aiohttp import multipart

from vj4 import app
from vj4 import error
from vj4.handler import base
from vj4.model import builtin
from vj4.model import fs
from vj4.model.adaptor import userfile


TEXT_FIELD_MAX_LENGTH = 2 ** 10
FILE_MAX_LENGTH = 2 ** 27 # 128 MiB
ALLOWED_MIMETYPE_PREFIX = ['image/', 'text/', 'application/zip']
HASHER = hashlib.md5


def check_type_and_name(field, name):
  if not isinstance(field, multipart.BodyPartReader):
    raise error.ValidationError(name)
  disptype, parts = multipart.parse_content_disposition(
    field.headers.get('Content-Disposition'))
  if disptype != 'form-data' or parts.get('name') != name:
    raise error.ValidationError(name)


async def handle_file_upload(self, form_fields=None, raise_error=True):
  """Handles file upload, fills form fields and returns file_id whose metadata.link is already increased."""
  reader = await self.request.multipart()
  try:
    # Check csrf token.
    if self.csrf_token:
      field = await reader.next()
      check_type_and_name(field, 'csrf_token')
      post_csrf_token = await field.read_chunk(len(self.csrf_token.encode()))
      if self.csrf_token.encode() != post_csrf_token:
        raise error.CsrfTokenError()

    # Read form fields.
    if form_fields:
      for k in form_fields:
        field = await reader.next()
        check_type_and_name(field, k)
        form_fields[k] = (await field.read_chunk(TEXT_FIELD_MAX_LENGTH)).decode()

    # Read file data.
    field = await reader.next()
    check_type_and_name(field, 'file')
    file_type = mimetypes.guess_type(field.filename)[0]
    if not file_type or not any(file_type.startswith(allowed_type)
                                for allowed_type in ALLOWED_MIMETYPE_PREFIX):
      raise error.FileTypeNotAllowedError('file', file_type)
    grid_in = None
    finally_delete = True
    try:
      grid_in = await fs.add(file_type)
      # Copy file data and check file length.
      size = 0
      chunk_size = max(field.chunk_size, 8192)
      chunk = await field.read_chunk(chunk_size)
      while chunk:
        size += len(chunk)
        if size > FILE_MAX_LENGTH:
          raise error.FileTooLongError('file')
        _, chunk = await asyncio.gather(grid_in.write(chunk), field.read_chunk(chunk_size))
      if chunk: # remaining
        await grid_in.write(chunk)
      if not size: # empty file
        raise error.ValidationError('file')
      await grid_in.close()
      # Deduplicate.
      file_id = await fs.link_by_md5(grid_in.md5, except_id=grid_in._id)
      if file_id:
        return file_id
      finally_delete = False
      return grid_in._id
    except:
      raise
    finally:
      if grid_in:
        await grid_in.close()
        if finally_delete:
          await fs.unlink(grid_in._id)
  except Exception:
    if raise_error:
      raise
    else:
      return None


@app.route('/fs/{secret:\w{40}}', 'fs_get')
class FsGetHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def stream_data(self, *, secret: str, headers_only: bool=False):
    grid_out = await fs.get_by_secret(secret)

    self.response.content_type = grid_out.content_type or 'application/octet-stream'
    self.response.content_length = grid_out.length

    # Cache control.
    self.response.last_modified = grid_out.upload_date
    self.response.headers['Etag'] = '"{0}"'.format(grid_out.md5)
    self.response.headers['Cache-Control'] = 'max-age=2592000' # 30 days = 2592000 seconds

    # Handle If-Modified-Since & If-None-Match.
    not_modified = False
    if self.request.if_modified_since:
      if_modified_since = self.request.if_modified_since.replace(tzinfo=None)
      last_modified = grid_out.upload_date.replace(microsecond=0)
      not_modified = not_modified or (last_modified <= if_modified_since)
    if self.request.headers.get('If-None-Match', ''):
      not_modified = not_modified \
        or ('"{0}"'.format(grid_out.md5) == self.request.headers.get('If-None-Match', ''))

    if not_modified:
      self.response.set_status(304, None) # Not Modified
      return

    if not headers_only:
      await self.response.prepare(self.request)
      # TODO(twd2): Range
      remaining = grid_out.length
      chunk = await grid_out.readchunk()
      while chunk and remaining >= len(chunk):
        self.response.write(chunk)
        remaining -= len(chunk)
        _, chunk = await asyncio.gather(self.response.drain(), grid_out.readchunk())
      if chunk:
        self.response.write(chunk[:remaining])
        await self.response.drain()
      await self.response.write_eof()

  head = functools.partialmethod(stream_data, headers_only=True)
  get = stream_data


@app.route('/fs/upload', 'fs_upload')
class FsUploadHandler(base.Handler):
  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.sanitize
  async def get(self):
    self.render('fs_upload.html', fdoc=None)

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.sanitize
  async def post(self):
    fields = collections.OrderedDict([('desc', '')])
    file_id = await handle_file_upload(self, fields)
    fdoc = await fs.get_meta(file_id) # TODO(twd2): join from handle_file_upload
    ufid = await userfile.add(fields['desc'], file_id, self.user['_id'], fdoc['length'])
    self.render('fs_upload.html', fdoc=fdoc, ufid=ufid)
