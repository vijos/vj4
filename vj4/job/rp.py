import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import domain
from vj4.model import user
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


@domainjob.wrap
async def run(domain_id: str):
  uddocs = domain.get_multi_users(domain_id, fields={'uid': 1, 'num_accept': 1})
  async for uddoc in uddocs:
    # TODO(twd2)
    await domain.set_user(domain_id, uddoc['uid'], rp=uddoc.get('num_accept', 0))
    # progress
    if uddoc['uid'] % 100 == 0:
      _logger.info('{0}: RP {1}'.format(uddoc['uid'], uddoc['num_accept']))


if __name__ == '__main__':
  argmethod.invoke_by_args()
