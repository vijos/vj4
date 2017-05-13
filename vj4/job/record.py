import asyncio
import collections
import functools
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


@argmethod.wrap
async def user_in_problem(uid: int, domain_id: str, pid: document.convert_doc_id):
  psdoc = await document.rev_init_status(domain_id, document.TYPE_PROBLEM, pid, uid)
  rdocs = record.get_multi(uid=uid, domain_id=domain_id, pid=pid,
                           type=constant.record.TYPE_SUBMISSION,
                           fields={'_id': 1, 'uid': 1,
                                   'status': 1, 'score': 1}).sort('_id', 1)
  new_psdoc = {'num_submit': 0, 'status': 0}
  async for rdoc in rdocs:
    new_psdoc['num_submit'] += 1
    if new_psdoc['status'] != constant.record.STATUS_ACCEPTED:
      new_psdoc['status'] = rdoc['status']
      new_psdoc['rid'] = rdoc['_id']
  _logger.info(repr(new_psdoc))
  if await document.rev_set_status(domain_id, document.TYPE_PROBLEM, pid, uid,
                                   psdoc['rev'], **new_psdoc):
    delta_submit = new_psdoc['num_submit'] - psdoc.get('num_submit', 0)
    if new_psdoc['status'] == constant.record.STATUS_ACCEPTED \
       and psdoc.get('status', 0) != constant.record.STATUS_ACCEPTED:
      delta_accept = 1
    elif new_psdoc['status'] != constant.record.STATUS_ACCEPTED \
         and psdoc.get('status', 0) == constant.record.STATUS_ACCEPTED:
      delta_accept = -1
    else:
      delta_accept = 0
    post_coros = []
    if delta_submit != 0:
      post_coros.append(problem.inc(domain_id, pid, 'num_submit', delta_submit))
      post_coros.append(domain.inc_user(domain_id, uid, num_submit=delta_submit))
    if delta_accept != 0:
      post_coros.append(problem.inc(domain_id, pid, 'num_accept', delta_accept))
      post_coros.append(domain.inc_user(domain_id, uid, num_accept=delta_accept))
    if post_coros:
      await asyncio.gather(*post_coros)


@domainjob.wrap
async def run(domain_id: str):
  _logger.info('Clearing previous statuses')
  await db.coll('document.status').update_many(
    {'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM},
    {'$unset': {'journal': '', 'rev': '', 'status': '', 'rid': '',
                'num_submit': '', 'num_accept': ''}})
  pdocs = problem.get_multi(domain_id=domain_id, fields={'_id': 1, 'doc_id': 1}).sort('doc_id', 1)
  dudoc_factory = functools.partial(dict, num_submit=0, num_accept=0)
  dudoc_updates = collections.defaultdict(dudoc_factory)
  status_coll = db.coll('document.status')
  async for pdoc in pdocs:
    _logger.info('Problem {0}'.format(pdoc['doc_id']))
    # TODO(twd2): ignore no effect statuses like system error, ...
    rdocs = record.get_multi(domain_id=domain_id, pid=pdoc['doc_id'],
                             type=constant.record.TYPE_SUBMISSION,
                             fields={'_id': 1, 'uid': 1,
                                     'status': 1, 'score': 1}).sort('_id', 1)
    _logger.info('Reading records, counting numbers, updating statuses')
    factory = functools.partial(dict, num_submit=0, num_accept=0, status=0, rid='')
    psdocs = collections.defaultdict(factory)
    pdoc_update = {'num_submit': 0, 'num_accept': 0}
    async for rdoc in rdocs:
      accept = True if rdoc['status'] == constant.record.STATUS_ACCEPTED else False
      pdoc_update['num_submit'] += 1
      psdocs[rdoc['uid']]['num_submit'] += 1
      dudoc_updates[rdoc['uid']]['num_submit'] += 1
      if psdocs[rdoc['uid']]['status'] != constant.record.STATUS_ACCEPTED:
        psdocs[rdoc['uid']]['status'] = rdoc['status']
        psdocs[rdoc['uid']]['rid'] = rdoc['_id']
        if accept:
          pdoc_update['num_accept'] += 1
          dudoc_updates[rdoc['uid']]['num_accept'] += 1
    status_bulk = status_coll.initialize_unordered_bulk_op()
    execute = False
    for uid, psdoc in psdocs.items():
      execute = True
      (status_bulk.find({'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM,
                         'doc_id': pdoc['doc_id'], 'uid': uid})
       .upsert().update_one({'$set': {**psdoc}}))
    if execute:
      _logger.info('Committing')
      await status_bulk.execute()
    _logger.info('Updating problem')
    await document.set(domain_id, document.TYPE_PROBLEM, pdoc['doc_id'], **pdoc_update)
  # users' num_submit, num_accept
  execute = False
  user_coll = db.coll('domain.user')
  user_bulk = user_coll.initialize_unordered_bulk_op()
  _logger.info('Updating users')
  for uid, dudoc_update in dudoc_updates.items():
    execute = True
    (user_bulk.find({'domain_id': domain_id, 'uid': uid})
     .upsert().update_one({'$set': dudoc_update}))
  if execute:
    _logger.info('Committing')
    await user_bulk.execute()


if __name__ == '__main__':
  argmethod.invoke_by_args()
