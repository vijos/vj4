import logging

from vj4 import db
from vj4 import constant
from vj4.model import document
from vj4.model.adaptor import problem
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


# base rp for each problem
RP_PROBLEM_BASE = 100.0
# minimum rp for each problem
RP_PROBLEM_MIN = 7.0
# rp calculate range
# (if count of accepted user is greater, will use RP_PROBLEM_MIN for this problem for each user)
RP_PROBLEM_MAX_USER = 1500
RP_MIN_DELTA = 10 ** (-9)


def modulus_problem(num_accept):
  return 0.7 * (0.9982119391 ** (num_accept - 1)) + 0.3


def modulus_user(order):
  return 0.8 * (0.9902396519 ** (order - 1)) + 0.2


def get_rp_func(pdoc):
  rp_base = RP_PROBLEM_BASE * modulus_problem(pdoc['num_accept'])
  if pdoc['num_accept'] <= RP_PROBLEM_MAX_USER:
    return lambda o: max(rp_base * modulus_user(o), RP_PROBLEM_MIN)
  else:
    return lambda o: RP_PROBLEM_MIN


def get_rp_expect(pdoc):
  new_pdoc = {'num_accept': pdoc['num_accept'] + 1}
  return get_rp_func(new_pdoc)(new_pdoc['num_accept'])


@argmethod.wrap
async def update_problem(domain_id: str, pid: document.convert_doc_id):
  uddoc_incs = {}
  pdoc = await problem.get(domain_id, pid)
  _logger.info('Domain {0} Problem {1}'.format(domain_id, pdoc['doc_id']))
  status_coll = db.Collection('document.status')
  status_bulk = status_coll.initialize_unordered_bulk_op()
  # Accepteds adjustment
  psdocs = problem.get_multi_status(domain_id=domain_id,
                                    doc_id=pdoc['doc_id'],
                                    status=constant.record.STATUS_ACCEPTED).sort('rid', 1)
  order = 0
  rp_func = get_rp_func(pdoc)
  async for psdoc in psdocs:
    order += 1
    rp = rp_func(order)
    delta_rp = rp - psdoc.get('rp', 0.0)
    status_bulk.find({'_id': psdoc['_id']}).update_one({'$set': {'rp': rp}})
    # (pid, uid) is unique.
    assert psdoc['uid'] not in uddoc_incs
    uddoc_incs[psdoc['uid']] = {'rp': delta_rp}
  if order != pdoc['num_accept']:
    _logger.warning('{0} != {1}'.format(order, pdoc['num_accept']))
    _logger.warning('Problem {0} num_accept may be inconsistent.'.format(pdoc['doc_id']))
  # Was Accepted but Now Not Accepteds adjustment
  # TODO(twd2): should we use $ne? can $ne be indexed?
  psdocs = problem.get_multi_status(domain_id=domain_id,
                                    doc_id=pdoc['doc_id'],
                                    status={'$gt': constant.record.STATUS_ACCEPTED},
                                    rp={'$gt': 0.0})
  execute = False
  async for psdoc in psdocs:
    rp = 0.0
    delta_rp = rp - psdoc['rp']
    execute = True
    status_bulk.find({'_id': psdoc['_id']}).update_one({'$set': {'rp': rp}})
    # (pid, uid) is unique.
    assert psdoc['uid'] not in uddoc_incs
    uddoc_incs[psdoc['uid']] = {'rp': delta_rp}
  if order > 0 or execute:
    _logger.info('Committing')
    await status_bulk.execute()
  # users' num_submit, num_accept
  user_coll = db.Collection('domain.user')
  user_bulk = user_coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Updating users')
  for uid, uddoc_inc in uddoc_incs.items():
    if abs(uddoc_inc['rp']) > RP_MIN_DELTA:
      execute = True
      user_bulk.find({'domain_id': domain_id, 'uid': uid}).upsert().update_one({'$inc': uddoc_inc})
  if execute:
    _logger.info('Committing')
    await user_bulk.execute()

@domainjob.wrap
async def recalc(domain_id: str):
  user_coll = db.Collection('domain.user')
  await user_coll.update({'domain_id': domain_id}, {'$set': {'rp': 0.0}}, multi=True)
  pdocs = problem.get_multi(domain_id=domain_id,
                            fields={'_id': 1, 'doc_id': 1, 'num_accept': 1}).sort('doc_id', 1)
  uddoc_updates = {}
  status_coll = db.Collection('document.status')
  async for pdoc in pdocs:
    _logger.info('Problem {0}'.format(pdoc['doc_id']))
    psdocs = problem.get_multi_status(domain_id=domain_id,
                                      doc_id=pdoc['doc_id'],
                                      status=constant.record.STATUS_ACCEPTED).sort('rid', 1)
    order = 0
    rp_func = get_rp_func(pdoc)
    status_bulk = status_coll.initialize_unordered_bulk_op()
    async for psdoc in psdocs:
      order += 1
      rp = rp_func(order)
      status_bulk.find({'_id': psdoc['_id']}).update_one({'$set': {'rp': rp}})
      if psdoc['uid'] not in uddoc_updates:
        uddoc_updates[psdoc['uid']] = {'rp': rp}
      else:
        uddoc_updates[psdoc['uid']]['rp'] += rp
    if order != pdoc['num_accept']:
      _logger.warning('{0} != {1}'.format(order, pdoc['num_accept']))
      _logger.warning('Problem {0} num_accept may be inconsistent.'.format(pdoc['doc_id']))
    if order > 0:
      _logger.info('Committing')
      await status_bulk.execute()
  # users' num_submit, num_accept
  user_bulk = user_coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Updating users')
  for uid, uddoc_update in uddoc_updates.items():
    execute = True
    user_bulk.find({'domain_id': domain_id, 'uid': uid}) \
             .upsert().update_one({'$set': uddoc_update})
  if execute:
    _logger.info('Committing')
    await user_bulk.execute()


if __name__ == '__main__':
  argmethod.invoke_by_args()
