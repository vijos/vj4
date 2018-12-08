import aiomongo
import functools
import urllib.parse

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='test', help='Database name.')
options.define('db_username', default='', help='Database username.')
options.define('db_password', default='', help='Database password.')
options.define('db_auth_source', default='',
               help='Database name associated with the user\'s credential.')


async def init():
  global _client, _db

  def escape(s):
    return urllib.parse.quote(s, safe='')

  url_parts = ['mongodb',
               escape(options.db_host),
               '/{}'.format(escape(options.db_name)),
               '', '']
  if options.db_username:  # add credentials
    url_parts[1] = ('{}:{}@'.format(escape(options.db_username), escape(options.db_password)))\
                   + url_parts[1]

  url_query_list = []
  if options.db_auth_source:
    url_query_list.append('authSource={}'.format(escape(options.db_auth_source)))

  url_parts[3]='&'.join(url_query_list)  # merge queries
  uri = urllib.parse.urlunsplit(tuple(url_parts))

  _client = await aiomongo.create_client(uri)
  _db = _client.get_database(options.db_name)


@functools.lru_cache()
def coll(name):
  return aiomongo.Collection(_db, name)


@functools.lru_cache()
def fs(name):
  return aiomongo.GridFS(_db, name)
