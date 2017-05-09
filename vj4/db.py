import aiomongo

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='test', help='Database name.')


class GridFS(object):
  _instances = {}

  def __new__(cls, name):
    if name not in cls._instances:
      cls._instances[name] = aiomongo.GridFS(db2, name)
    return cls._instances[name]


async def init_db2():
  client = await aiomongo.create_client('mongodb://' + options.db_host)
  global db2
  db2 = client.get_database(options.db_name)
