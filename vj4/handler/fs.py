import asyncio
import collections
import functools
import hashlib
import mimetypes
import tempfile
from aiohttp import multipart

from vj4 import app
from vj4 import error
from vj4.handler import base
from vj4.model import builtin
from vj4.model import fs


TEXT_FIELD_MAX_LENGTH = 2 ** 10
FILE_MAX_LENGTH = 2 ** 27 # 128MiB
ALLOWED_MIMETYPE_PREFIX = ['image/', 'text/', 'application/zip']


def check_type_and_name(field, name):
  if not isinstance(field, multipart.BodyPartReader):
    raise error.ValidationError(name)
  disptype, parts = multipart.parse_content_disposition(
    field.headers.get('Content-Disposition'))
  if disptype != 'form-data' or parts.get('name') != name:
    raise error.ValidationError(name)


async def handle_file_upload(self, form_fields=None, raise_error=True):
  ''' Handles file upload, fills form fields and returns file_id. '''
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
    with tempfile.TemporaryFile() as tmp:
      hasher = hashlib.md5()
      size = 0
      while True:
        chunk = await field.read_chunk(max(field.chunk_size, 8192))
        if not chunk:
          break
        size += len(chunk)
        if size > FILE_MAX_LENGTH:
          raise error.FileTooLongError('file')
        hasher.update(chunk)
        tmp.write(chunk)
      if not size: # empty file
        raise error.ValidationError('file')

      tmp.seek(0)
      md5 = hasher.hexdigest()
      file_id = await fs.link_by_md5(md5)
      if not file_id:
        file_id = await fs.add_file_object(file_type, tmp)
      return file_id
  except Exception:
    await self.request.release()
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
    self.render('fs_upload.html')

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.sanitize
  async def post(self):
    fields = collections.OrderedDict([('title', '')])
    file_id = await handle_file_upload(self, fields)
    self.response.text = str(file_id)
    # TODO(twd2): UI
    # self.json_or_redirect(self.url)
