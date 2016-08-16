import logging

from vj4.model import builtin
from vj4.model import domain
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


def wrap(method):
  async def run(domain_id: str=None):
    _logger.info('Built in domains')
    for ddoc in builtin.DOMAINS:
      _logger.info('Domain: {0}'.format(ddoc['_id']))
      await method(ddoc['_id'])
    _logger.info('User domains')
    ddocs = domain.get_multi({'_id': 1})
    async for ddoc in ddocs:
      _logger.info('Domain: {0}'.format(ddoc['_id']))
      await method(ddoc['_id'])

  if method.__module__ == '__main__':
    argmethod._methods[method.__name__] = method
    argmethod._methods[method.__name__ + '_all'] = run
  return run
