import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import domain
from vj4.model import user
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


def _count_level(perc):
  perc *= 100
  for level, value in builtin.LEVELS:
    if perc <= value:
      return level

def _process_domain(domain_id, keyword, rank_field, level_field):
  _logger.info('Domain {0}'.format(domain_id))
  # TODO(twd2): per domain?
  uddocs = domain.get_multi_users(domain_id, fields={'uid': 1, keyword: 1}).sort([(keyword, -1)])
  last_udoc = {keyword: -999}
  rank = 0
  async for udoc in udocs:
    if udoc[keyword] != last_udoc[keyword]:
      rank += 1
    await user.set_by_uid(udoc['_id'], rank=rank)
    last_udoc = udoc
    _logger.info('{0}: Rank {1}'.format(udoc['uname'], rank))
  udocs = user.get_multi({'_id': 1, 'uname': 1, keyword: 1, 'rank': 1}).sort([(keyword, -1)])
  async for udoc in udocs:
    level = _count_level(udoc['rank'] / rank)
    await user.set_by_uid(udoc['_id'], level=level)
    _logger.info('{0}: Level {1}'.format(udoc['uname'], level))

@argmethod.wrap
async def rank(keyword: str='rp', rank_field: str='rank', level_field: str='level'):
  _logger.info('built in domains')
  for ddoc in builtin.DOMAINS:
    await _process_domain(ddoc['_id'], keyword, rank_field, level_field)
  _logger.info('user domains')
  ddocs = domain.get_multi({'_id': 1})
  async for ddoc in ddocs:
    await _process_domain(ddoc['_id'], keyword, rank_field, level_field)

if __name__ == '__main__':
  argmethod.invoke_by_args()
