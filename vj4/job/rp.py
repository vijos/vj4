import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import domain
from vj4.model import user
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


async def _process_domain(domain_id):
  _logger.info('Domain {0}'.format(domain_id))
  uddocs = domain.get_multi_users(domain_id, fields={'uid': 1, 'num_accept': 1})
  async for uddoc in uddocs:
    # TODO(twd2)
    await domain.set_user(domain_id, uddoc['uid'], rp=uddoc.get('num_accept', 0))
    # progress
    if uddoc['uid'] % 100 == 0:
      _logger.info('{0}: RP {1}'.format(uddoc['uid'], uddoc['num_accept']))


@argmethod.wrap
async def rp():
  _logger.info('Built in domains')
  for ddoc in builtin.DOMAINS:
    await _process_domain(ddoc['_id'])
  _logger.info('User domains')
  ddocs = domain.get_multi({'_id': 1})
  async for ddoc in ddocs:
    await _process_domain(ddoc['_id'])


if __name__ == '__main__':
  argmethod.invoke_by_args()
