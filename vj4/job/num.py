import asyncio
import logging

from vj4 import db
from vj4.model import builtin
from vj4.model import domain
from vj4.model import document
from vj4.model.adaptor import discussion
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


@domainjob.wrap
async def discussion(domain_id: str):
  _logger.info('Discussion')
  pipeline = [
    {
      '$match': {'domain_id': domain_id, 'doc_type': document.TYPE_DISCUSSION_REPLY}
    },
    {
      '$group': {
        '_id': '$parent_doc_id',
        'num_replies': {'$sum': 1}
      }
    }
  ]
  coll = db.coll('document')
  await coll.update_many({'domain_id': domain_id, 'doc_type': document.TYPE_DISCUSSION},
                         {'$set': {'num_replies': 0}})
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document').aggregate(pipeline):
    bulk.find({'domain_id': domain_id,
               'doc_type': document.TYPE_DISCUSSION,
               'doc_id': adoc['_id']}) \
        .update_one({'$set': {'num_replies': adoc['num_replies']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()


@domainjob.wrap
async def contest(domain_id: str):
  _logger.info('Contest')
  pipeline = [
    {
      '$match': {'domain_id': domain_id, 'doc_type': document.TYPE_CONTEST}
    },
    {
      '$group': {
        '_id': '$doc_id',
        'attend': {'$sum': '$attend'}
      }
    }
  ]
  coll = db.coll('document')
  await coll.update_many({'domain_id': domain_id, 'doc_type': document.TYPE_CONTEST},
                         {'$set': {'attend': 0}})
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document.status').aggregate(pipeline):
    bulk.find({'domain_id': domain_id,
               'doc_type': document.TYPE_CONTEST,
               'doc_id': adoc['_id']}) \
        .update_one({'$set': {'attend': adoc['attend']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()


@domainjob.wrap
async def training(domain_id: str):
  _logger.info('Training')
  pipeline = [
    {
      '$match': {'domain_id': domain_id, 'doc_type': document.TYPE_TRAINING}
    },
    {
      '$group': {
        '_id': '$doc_id',
        'enroll': {'$sum': '$enroll'}
      }
    }
  ]
  coll = db.coll('document')
  await coll.update_many({'domain_id': domain_id, 'doc_type': document.TYPE_TRAINING},
                         {'$set': {'enroll': 0}})
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document.status').aggregate(pipeline):
    bulk.find({'domain_id': domain_id,
               'doc_type': document.TYPE_TRAINING,
               'doc_id': adoc['_id']}) \
        .update_one({'$set': {'enroll': adoc['enroll']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()


@domainjob.wrap
async def problem(domain_id: str):
  _logger.info('Problem')
  pipeline = [
    {
      '$match': {'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM}
    },
    {
      '$group': {
        '_id': '$owner_uid',
        'num_problems': {'$sum': 1}
      }
    }
  ]
  user_coll = db.coll('domain.user')
  await user_coll.update_many({'domain_id': domain_id},
                              {'$set': {'num_problems': 0}})
  user_coll = user_coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document').aggregate(pipeline):
    user_coll.find({'domain_id': domain_id,
                    'uid': adoc['_id']}) \
             .upsert().update_one({'$set': {'num_problems': adoc['num_problems']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await user_coll.execute()


@domainjob.wrap
async def problem_solution(domain_id: str):
  _logger.info('Problem Solution Votes')
  pipeline = [
    {
      '$match': {'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM_SOLUTION}
    },
    {
      '$group': {
        '_id': '$doc_id',
        'vote': {'$sum': '$vote'}
      }
    }
  ]
  coll = db.coll('document')
  await coll.update_many({'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM_SOLUTION},
                         {'$set': {'vote': 0}})
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document.status').aggregate(pipeline):
    bulk.find({'domain_id': domain_id,
               'doc_type': document.TYPE_PROBLEM_SOLUTION,
               'doc_id': adoc['_id']}) \
        .update_one({'$set': {'vote': adoc['vote']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()

  _logger.info('Problem Solution Votes group by user')
  pipeline = [
    {
      '$match': {'domain_id': domain_id, 'doc_type': document.TYPE_PROBLEM_SOLUTION}
    },
    {
      '$group': {
        '_id': '$owner_uid',
        'num_liked': {'$sum': '$vote'}
      }
    }
  ]
  user_coll = db.coll('domain.user')
  await user_coll.update_many({'domain_id': domain_id},
                              {'$set': {'num_liked': 0}})
  user_bulk = user_coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Counting')
  async for adoc in await db.coll('document').aggregate(pipeline):
    user_bulk.find({'domain_id': domain_id,
                    'uid': adoc['_id']}) \
             .upsert().update_one({'$set': {'num_liked': adoc['num_liked']}})
    execute = True
  if execute:
    _logger.info('Committing')
    await user_bulk.execute()


@domainjob.wrap
async def num(domain_id: str):
  await asyncio.gather(discussion(domain_id), contest(domain_id), training(domain_id),
                       problem(domain_id), problem_solution(domain_id))


if __name__ == '__main__':
  argmethod.invoke_by_args()
