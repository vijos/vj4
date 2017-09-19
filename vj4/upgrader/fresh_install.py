import logging

from vj4.model import system
from vj4.util import argmethod


_logger = logging.getLogger(__name__)


@argmethod.wrap
async def run():
  lock = await system.acquire_upgrade_lock()
  try:
    await system.ensure_db_version(0)
    await system.set_db_version(system.EXPECTED_DB_VERSION)
    _logger.info('Initialize complete!')
  finally:
    await system.release_upgrade_lock(lock)


if __name__ == '__main__':
  argmethod.invoke_by_args()
