import logging
import pkgutil
from os import path

from vj4.util import argmethod
from vj4.util import options

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


def get_remote_ip(request):
  if options.ip_header:
    return request.headers.get(options.ip_header)
  else:
    return request.transport.get_extra_info('peername')[0]


if __name__ == '__main__':
  argmethod.invoke_by_args()
