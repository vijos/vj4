import logging
import pkgutil
from os import path

from vj4.util import argmethod
import re

_logger = logging.getLogger(__name__)


@argmethod.wrap
async def ensure_all_indexes():
  model_path = path.join(path.dirname(path.dirname(__file__)), 'model')
  for module_finder, name, ispkg in pkgutil.iter_modules([model_path]):
    if not ispkg:
      module = module_finder.find_module(name).load_module()
      if 'ensure_indexes' in dir(module):
        _logger.info('Ensuring indexes for "%s".' % name)
        await module.ensure_indexes()


@argmethod.wrap
def extract_duplicate_key_errmsg(msg):
  vals = re.findall('"(.+?)"', msg)
  index_name = msg[msg.find('index:') + 6:msg.find('dup key:')].strip()
  keys = re.findall('_(\w+?)_\d', '_' + index_name)
  return dict(zip(keys, vals))


if __name__ == '__main__':
  argmethod.invoke_by_args()
