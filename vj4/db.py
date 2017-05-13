import aiomongo
import functools

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='test', help='Database name.')


async def init():
  client = await aiomongo.create_client('mongodb://' + options.db_host)
  global _db
  _db = client.get_database(options.db_name)


@functools.lru_cache()
def coll(name):
  return aiomongo.Collection(_db, name)


@functools.lru_cache()
def fs(name):
  return aiomongo.GridFS(_db, name)
