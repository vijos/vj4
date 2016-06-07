from motor import motor_asyncio

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_name', default='test', help='Database name.')


class Database(object):
  _instance = None

  def __new__(cls):
    if not cls._instance:
      client = motor_asyncio.AsyncIOMotorClient(options.options.db_host)
      cls._instance = motor_asyncio.AsyncIOMotorDatabase(client, options.options.db_name)
    return cls._instance


class Collection(object):
  _instances = {}

  def __new__(cls, name):
    if name not in cls._instances:
      cls._instances[name] = motor_asyncio.AsyncIOMotorCollection(Database(), name)
    return cls._instances[name]


class GridFS(object):
  _instances = {}

  def __new__(cls, name):
    if name not in cls._instances:
      cls._instances[name] = motor_asyncio.AsyncIOMotorGridFS(Database(), name)
    return cls._instances[name]
