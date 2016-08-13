import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import user
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


# Key represents level
# Value represents percent
# E.g. 10: 1 means that people who rank in 1% will get 10 levels
LEVEL_CONFIG = [
  (10, 1),
  (9, 2),
  (8, 3),
  (7, 5),
  (6, 10),
  (5, 20),
  (4, 30),
  (3, 50),
  (2, 80),
  (1, 100)]

def _count_level(perc):
  perc *= 100
  for level, value in LEVEL_CONFIG:
    if perc <= value:
      return level

@argmethod.wrap
async def rank(keyword: str='rp'):
  # TODO(twd2): per domain?
  udocs = user.get_multi({'_id': 1, 'uname': 1, keyword: 1}).sort([(keyword, -1)])
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

if __name__ == '__main__':
  argmethod.invoke_by_args()
