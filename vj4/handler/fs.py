import asyncio
import functools
import hashlib

from vj4 import app
from vj4.handler import base
from vj4.model import builtin
from vj4.model import fs


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
  @base.post_argument
  @base.require_csrf_token
  @base.sanitize
  async def post(self, file: lambda _: _):
    # TODO(twd2): check file size
    fid = ''
    if file:
      data = file.file.read()
      md5 = hashlib.md5(data).hexdigest()
      fid = await fs.link_by_md5(md5)
      if not fid:
        # TODO(twd2): mimetype
        fid = await fs.add_data('application/zip', data)
    self.response.text = str(fid)
    # TODO(twd2): UI
    # self.json_or_redirect(self.url)
