"""Recalcuates num_submit and num_accept in problem status."""
import asyncio

from vj4 import constant
from vj4 import db
from vj4.model import document


async def main():
  pipeline = [
    {
      '$match': {'hidden': False, 'type': constant.record.TYPE_SUBMISSION}
    },
    {
      '$group': {
        '_id': {'domain_id': '$domain_id', 'pid': '$pid', 'uid': '$uid'},
        'num_submit': {'$sum': 1},
        'num_accept': {
          '$sum': {
            '$cond': [{'$eq': ['$status', constant.record.STATUS_ACCEPTED]}, 1, 0]
          }
        }
      }
    },
    {
      '$group': {
        '_id': {'domain_id': '$_id.domain_id', 'pid': '$_id.pid'},
        'num_submit': {'$sum': '$num_submit'},
        'num_accept': {'$sum': {'$min': ['$num_accept', 1]}}
      }
    },
  ]

  bulk = db.coll('document').initialize_unordered_bulk_op()
  async for adoc in db.coll('record').aggregate(pipeline):
    bulk.find({'domain_id': adoc['_id']['domain_id'],
               'doc_type': document.TYPE_PROBLEM,
               'doc_id': adoc['_id']['pid']}) \
        .update_one({'$set': {'num_submit': adoc['num_submit'],
                              'num_accept': adoc['num_accept']}})
  await bulk.execute()

if __name__ == '__main__':
  asyncio.get_event_loop().run_until_complete(main())
