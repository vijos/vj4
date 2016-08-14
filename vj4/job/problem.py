import logging

from vj4 import db
from vj4 import constant
from vj4.model import builtin
from vj4.model import domain
from vj4.model import document
from vj4.model import record
from vj4.model.adaptor import problem
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


@argmethod.wrap
async def status():
  await db.Collection('document').update(
    {'doc_type': document.TYPE_PROBLEM},
    {'$set': {'num_submit': 0, 'num_accept': 0}}, multi=True)
  await db.Collection('document.status').update(
    {'doc_type': document.TYPE_PROBLEM},
    {'$unset': {'status': '', 'rid': ''}}, multi=True)
  rdocs = record.get_all_multi().sort('_id', 1)
  record_count = await rdocs.count()
  i = 0
  async for rdoc in rdocs:
    accept = True if rdoc['status'] == constant.record.STATUS_ACCEPTED else False
    do_inc = await problem.update_status(rdoc['domain_id'], rdoc['pid'], rdoc['uid'],
                                         rdoc['_id'], rdoc['status'])
    if do_inc:
      await problem.inc(rdoc['domain_id'], rdoc['pid'], 1, 1 if accept else 0)
    # TODO(twd2): update user (num_submit, num_accept)
    i += 1
    if i % 5000 == 0:
      _logger.info('#{0} {1}%'.format(i, 100 * i / record_count))

if __name__ == '__main__':
  argmethod.invoke_by_args()
