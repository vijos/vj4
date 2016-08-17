import logging

from vj4 import db
from vj4 import constant
from vj4.model import builtin
from vj4.model import document
from vj4.model import domain
from vj4.model.adaptor import problem
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


# base rp for each problem
RP_PROBLEM_BASE = 100.0
# minimum rp for each problem
RP_PROBLEM_MIN = 7.0
# rp calculate range
# (if count of accepted user is greater, will use RP_PROBLEM_MIN for the problem)
RP_PROBLEM_MAX_USER = 1500


def modulus_problem(num_accept):
  return 0.7 * (0.9982119391 ** num_accept) + 0.3


def modulus_user(order):
  return 0.8 * (0.9902396519 ** order) + 0.2


@domainjob.wrap
async def run(domain_id: str):
  pdocs = problem.get_multi(domain_id, {'_id': 1, 'doc_id': 1, 'num_accept': 1}).sort('doc_id', 1)
  uddoc_updates = {}
  async for pdoc in pdocs:
    _logger.info('Problem {0}'.format(pdoc['doc_id']))
    psdocs = problem.get_multi_status(domain_id, doc_id=pdoc['doc_id'],
                                      status=constant.record.STATUS_ACCEPTED).sort('rid', 1)
    order = 0
    rp_base = RP_PROBLEM_BASE * modulus_problem(pdoc['num_accept'])
    if pdoc['num_accept'] <= RP_PROBLEM_MAX_USER:
      rp_func = lambda o: max(rp_base * modulus_user(o), RP_PROBLEM_MIN)
    else:
      rp_func = lambda o: RP_PROBLEM_MIN
    async for psdoc in psdocs:
      order += 1
      rp = rp_func(order)
      await document.set_status(domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], psdoc['uid'],
                                rp=rp)
      if psdoc['uid'] not in uddoc_updates:
        uddoc_updates[psdoc['uid']] = {'rp': rp}
      else:
        uddoc_updates[psdoc['uid']]['rp'] += rp
    if order != pdoc['num_accept']:
      _logger.warning('Problem {0} num_accept may be inconsistent.'.format(pdoc['doc_id']))
  _logger.info('Updating users')
  for uid, uddoc_update in uddoc_updates.items():
    await domain.set_user(domain_id, uid, **uddoc_update)


if __name__ == '__main__':
  argmethod.invoke_by_args()
