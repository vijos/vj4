import logging
import pkgutil
from os import path
from functools import reduce

from vj4.util import argmethod

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


def dedupe(list):
  result = []
  result_set = set()
  for i in list:
    if i in result_set:
      continue
    result.append(i)
    result_set.add(i)
  return result


if __name__ == '__main__':
  argmethod.invoke_by_args()
