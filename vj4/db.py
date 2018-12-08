import aiomongo
import functools
import urllib.parse
from yarl import URL

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_port', default=27017, help='Database port.')
options.define('db_name', default='test', help='Database name.')
options.define('db_username', default='', help='Database username.')
options.define('db_password', default='', help='Database password.')
options.define('db_auth_source', default='',
               help='Database name associated with the user\'s credential.')


async def init():
  global _client, _db

  url_parts = {
    'scheme': 'mongodb',
    'host': options.db_host,
    'path': options.db_name,
    'port': options.db_port,
    'user': options.db_username,
    'password': options.db_password,
    'query': {}
  }
  if options.db_auth_source:
    url_parts['query']['authSource'] = options.db_auth_source
  url = URL.build(**url_parts)

  _client = await aiomongo.create_client(str(url))
  _db = _client.get_database(options.db_name)


@functools.lru_cache()
def coll(name):
  return aiomongo.Collection(_db, name)


@functools.lru_cache()
def fs(name):
  return aiomongo.GridFS(_db, name)
