import aiomongo
import functools
import urllib.parse

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='test', help='Database name.')
options.define('db_username', default='', help='Database username.')
options.define('db_password', default='', help='Database password.')


async def init():
  global _client, _db

  def escape(s):
    return urllib.parse.quote(s, safe='')

  if not options.db_username:
    uri = 'mongodb://{}'.format(escape(options.db_host))
  else:
    uri = 'mongodb://{}:{}@{}/?authSource={}'.format(escape(options.db_username),
                                                     escape(options.db_password),
                                                     escape(options.db_host),
                                                     escape(options.db_name))
  _client = await aiomongo.create_client(uri)
  _db = _client.get_database(options.db_name)


@functools.lru_cache()
def coll(name):
  return aiomongo.Collection(_db, name)


@functools.lru_cache()
def fs(name):
  return aiomongo.GridFS(_db, name)
