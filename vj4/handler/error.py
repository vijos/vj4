from vj4 import error
from vj4.handler import base


class NotFoundHandler(base.Handler):
  async def get(self):
    raise error.NotFoundError(self.url)
