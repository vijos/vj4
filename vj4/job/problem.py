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


_logger = logging.getLogger(__name__)


async def _process_domain(domain_id, udocs):
  _logger.info('domain {0}'.format(domain_id))
  pdocs = problem.get_multi(domain_id, {'_id': 1, 'doc_id': 1}).sort('_id', 1)
  udoc_updates = {}
  async for pdoc in pdocs:
    _logger.info('problem {0}'.format(pdoc['doc_id']))
    rdocs = record.get_problem_multi(domain_id, pdoc['doc_id'],
                                     fields={'_id': 1, 'uid': 1,
                                             'status': 1, 'score': 1}).sort('_id', 1)
    _logger.info('reading records, rebuilding journals')
    psdocs = {}
    async for rdoc in rdocs:
      accept = True if rdoc['status'] == constant.record.STATUS_ACCEPTED else False
      j = {'rid': rdoc['_id'], 'accept': accept, 'status': rdoc['status'], 'score': rdoc['score']}
      if rdoc['uid'] not in psdocs:
        psdocs[rdoc['uid']] = {'journal': [j]}
      else:
        psdocs[rdoc['uid']]['journal'].append(j)
    _logger.info('counting numbers')
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
    _logger.info('updating problem')
    await document.set(domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], **pdoc_update)
    _logger.info('updating users')
    for uid, udoc_update in udoc_updates.items():
      # TODO(twd2): update user (num_submit, num_accept)
      # await domain.set_user(domain_id, uid, **udoc_update)
      pass


@argmethod.wrap
async def status():
  _logger.info('clearing previous statuses')
  await asyncio.gather(
    db.Collection('document').update(
      {'doc_type': document.TYPE_PROBLEM},
      {'$set': {'num_submit': 0, 'num_accept': 0}}, multi=True),
    db.Collection('document.status').update(
      {'doc_type': document.TYPE_PROBLEM},
      {'$unset': {'journal': '', 'rev': '', 'status': '', 'rid': '',
                  'num_submit': '', 'num_accept': ''}}, multi=True))
  _logger.info('loading users')
  udocs = await user.get_multi({'_id': 1}).to_list(None)
  _logger.info('built in domains')
  for ddoc in builtin.DOMAINS:
    await _process_domain(ddoc['_id'], udocs)
  _logger.info('user domains')
  ddocs = domain.get_multi({'_id': 1})
  async for ddoc in ddocs:
    await _process_domain(ddoc['_id'], udocs)


if __name__ == '__main__':
  argmethod.invoke_by_args()
