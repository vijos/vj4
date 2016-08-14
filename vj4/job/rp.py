import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import user
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


@argmethod.wrap
async def rp():
  # TODO(twd2)
  _logger.info('TODO')

if __name__ == '__main__':
  argmethod.invoke_by_args()
