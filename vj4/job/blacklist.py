import logging
from vj4 import db
from vj4.model import blacklist
from vj4.model import document
from vj4.model import user
from vj4.model.adaptor import discussion
from vj4.util import argmethod
from vj4.util import options

options.define('dryrun', default=True, help='Dry run.')

_logger = logging.getLogger(__name__)


@argmethod.wrap
def address(ip: str):
  return _address(ip, set(), set(), set())


@argmethod.wrap
def discuss(domain_id: str, did: document.convert_doc_id):
  return _discussion(domain_id, did, set(), set(), set())


@argmethod.wrap
def usr(uid: int):
  return _user(uid, set(), set(), set())


async def _address(ip, bset, uset, dset):
  if ip in bset:
    return
  bset.add(ip)
  _logger.info("ip %s", ip)
  async for udoc in db.coll('user').find({'loginip': ip}, {'_id': 1}):
    await _user(udoc['_id'], bset, uset, dset)
  if not options.dryrun:
    await blacklist.add(ip)


async def _discussion(domain_id, did, bset, uset, dset):
  if did in dset:
    return
  dset.add(did)
  ddoc = await discussion.get(domain_id, did)
  if not ddoc:
    return
  _logger.info("discussion %s", ddoc['title'])
  await _user(ddoc['owner_uid'], bset, uset, dset)
  if 'ip' in ddoc:
    await _address(ddoc['ip'], bset, uset, dset)
  if not options.dryrun:
    await discussion.delete(domain_id, ddoc['doc_id'])


async def _user(uid, bset, uset, dset):
  if uid in uset:
    return
  uset.add(uid)
  udoc = await user.get_by_uid(uid)
  if not udoc:
    return
  _logger.info('user %s %s', udoc['_id'], udoc['uname'])
  await _address(udoc['loginip'], bset, uset, dset)
  async for ddoc in db.coll('document').find({
      'doc_type': document.TYPE_DISCUSSION,
      'owner_uid': uid}, {'domain_id': 1, 'doc_id': 1}):
    await _discussion(ddoc['domain_id'], ddoc['doc_id'], bset, uset, dset)


if __name__ == '__main__':
  argmethod.invoke_by_args()
