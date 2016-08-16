import asyncio
import logging

from vj4 import db
from vj4 import constant
from vj4.model import builtin
from vj4.model import domain
from vj4.model import document
from vj4.model import record
from vj4.model import user
from vj4.model.adaptor import problem
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


@domainjob.wrap
async def run(domain_id: str):
  _logger.info('Clearing previous statuses')
  await db.Collection('document.status').update(
    {'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM},
    {'$unset': {'journal': '', 'rev': '', 'status': '', 'rid': '',
                'num_submit': '', 'num_accept': ''}}, multi=True)
  pdocs = problem.get_multi(domain_id, {'_id': 1, 'doc_id': 1}).sort('doc_id', 1)
  udoc_updates = {}
  async for pdoc in pdocs:
    _logger.info('Problem {0}'.format(pdoc['doc_id']))
    rdocs = record.get_problem_multi(domain_id, pdoc['doc_id'],
                                     fields={'_id': 1, 'uid': 1,
                                             'status': 1, 'score': 1}).sort('_id', 1)
    _logger.info('Reading records, rebuilding journals')
    psdocs = {}
    async for rdoc in rdocs:
      accept = True if rdoc['status'] == constant.record.STATUS_ACCEPTED else False
      j = {'rid': rdoc['_id'], 'accept': accept, 'status': rdoc['status'], 'score': rdoc['score']}
      if rdoc['uid'] not in psdocs:
        psdocs[rdoc['uid']] = {'journal': [j]}
      else:
        psdocs[rdoc['uid']]['journal'].append(j)
    _logger.info('Counting numbers')
    pdoc_update = {'num_submit': 0, 'num_accept': 0}
    for uid, psdoc in psdocs.items():
      status = problem._stat_func(psdoc['journal'])
      pdoc_update['num_submit'] += status['num_submit']
      pdoc_update['num_accept'] += status['num_accept']
      await document.set_status(domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], uid,
                                **status)
      if uid not in udoc_updates:
        udoc_updates[uid] = {'num_submit': status['num_submit'],
                             'num_accept': status['num_accept']}
      else:
        udoc_updates[uid]['num_submit'] += status['num_submit']
        udoc_updates[uid]['num_accept'] += status['num_accept']
    _logger.info('Updating problem')
    await document.set(domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], **pdoc_update)
  _logger.info('Updating users')
  for uid, udoc_update in udoc_updates.items():
    await domain.set_user(domain_id, uid, **udoc_update)


if __name__ == '__main__':
  argmethod.invoke_by_args()
