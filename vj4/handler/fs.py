import asyncio
import functools
import mimetypes
from bson import objectid

from vj4 import app
from vj4 import error
from vj4.handler import base
from vj4.model import builtin
from vj4.model import fs
from vj4.model.adaptor import userfile

FILE_MAX_LENGTH = 2 ** 27 # 128 MiB
USER_QUOTA = 2 ** 27 # 128 MiB
ALLOWED_MIMETYPE_PREFIX = ['image/', 'text/', 'application/zip']


@app.route('/fs/{secret:\w{40}}', 'fs_get', global_route=True)
class FsGetHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def stream_data(self, *, secret: str, headers_only: bool=False):
    grid_out = await fs.get_by_secret(secret)

    self.response.content_type = grid_out.content_type or 'application/octet-stream'
    # FIXME(iceboy): For some reason setting response.content_length doesn't work in aiohttp 2.0.6.
    self.response.headers['Content-Length'] = str(grid_out.length)
    ext = mimetypes.guess_extension(self.response.content_type)
    if not ext:
      ext = ''
    self.response.headers.add('Content-Disposition',
                              'attachment; filename="{}{}"'.format(secret, ext))

    # Cache control.
    self.response.last_modified = grid_out.upload_date
    self.response.headers['Etag'] = '"{}"'.format(grid_out.md5)
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
        remaining -= len(chunk)
        _, chunk = await asyncio.gather(self.response.write(chunk), grid_out.readchunk())
      if chunk:
        await self.response.write(chunk[:remaining])
      await self.response.write_eof()

  head = functools.partialmethod(stream_data, headers_only=True)
  get = stream_data


@app.route('/fs/upload', 'fs_upload', global_route=True)
class FsUploadHandler(base.Handler):
  def get_content_type(self, filename):
    content_type = mimetypes.guess_type(filename)[0]
    if not content_type or not any(content_type.startswith(allowed_type)
                                   for allowed_type in ALLOWED_MIMETYPE_PREFIX):
      raise error.FileTypeNotAllowedError(filename, content_type)
    return content_type

  def get_quota(self):
    quota = USER_QUOTA
    if self.has_priv(builtin.PRIV_UNLIMITED_QUOTA):
      quota = 2 ** 63 - 1
    return quota

  @base.require_priv(builtin.PRIV_USER_PROFILE | builtin.PRIV_CREATE_FILE)
  async def get(self):
    self.render('fs_upload.html', fdoc=None,
                usage=await userfile.get_usage(self.user['_id']),
                quota=self.get_quota())

  @base.require_priv(builtin.PRIV_USER_PROFILE | builtin.PRIV_CREATE_FILE)
  @base.multipart_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, *, desc: str, file: objectid.ObjectId):
    quota = self.get_quota()
    fdoc = await fs.get_meta(file)
    ufdoc = await userfile.inc_usage(self.user['_id'], fdoc['length'], quota)
    try:
      ufid = await userfile.add(desc, file, self.user['_id'], fdoc['length'])
    except:
      await userfile.dec_usage(self.user['_id'], fdoc['length'])
      raise
    self.render('fs_upload.html', fdoc=fdoc, ufid=ufid,
                usage=ufdoc['usage_userfile'], quota=quota)
