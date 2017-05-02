import aiomongo
from motor import motor_asyncio

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='test', help='Database name.')


class Database(object):
  _instance = None

  def __new__(cls):
    if not cls._instance:
      client = motor_asyncio.AsyncIOMotorClient(options.db_host)
      cls._instance = motor_asyncio.AsyncIOMotorDatabase(client, options.db_name)
    return cls._instance


class GridFS(object):
  _instances = {}

  def __new__(cls, name):
    if name not in cls._instances:
      cls._instances[name] = motor_asyncio.AsyncIOMotorGridFS(Database(), name)
    return cls._instances[name]


async def init_db2():
  client = await aiomongo.create_client('mongodb://' + options.db_host)
  global db2
  db2 = client.get_database(options.db_name)
