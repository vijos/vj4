import pymongo
import pymongo.errors

from vj4.util import options

options.define('db_host', default='localhost', help='Database hostname or IP address.')
options.define('db_port', default=27017, help='Database port.')
options.define('db_name', default='test', help='Database name.')

# Key represents level
# Value represents percent
# E.g. 10: 1 means that people who rank in 1% will get 10 levels
level_config = [
    (10, 1),
    (9, 2),
    (8, 3),
    (7, 5),
    (6, 10),
    (5, 20),
    (4, 30),
    (3, 50),
    (2, 80),
    (1, 100)
  ]

def rank_data(udocs):
  stack = list()
  result = list()
  rank = 1
  for udoc in udocs:
    if not stack:
      stack.append(udoc)
    elif udoc['rp'] == stack[-1]['rp']:
      stack.append(udoc)
    else:
      while stack:
        doc = stack.pop()
        result.append(rank)
      rank += 1
      stack.append(udoc)

  while stack:
    doc = stack.pop()
    result.append(rank)

  return result

def count_level(perc):
  global level_config

  perc *= 100

  for key, value in level_config:
    if perc <= value:
      return key

def rank():
  conn = pymongo.MongoClient(options.options.db_host, options.options.db_port)
  db = conn[options.options.db_name]
  coll = db['user']

  udocs = coll.find().sort([('rp', -1)])

  rank_array = rank_data(udocs)
  total = rank_array[-1]

  bulk = coll.initialize_unordered_bulk_op()

  # reset cursor
  udocs.rewind()
  for udoc, rankN in zip(udocs, rank_array):
    level = count_level(rankN / total)

    bulk.find({'_id':udoc['_id']}).update_one(
      {'$set':
        {
          'rankN':rankN,
          'level':level
          }})

  try:
    bulk.execute()
  except pymongo.errors.BulkWriteError as bwe:
    pprint(bwe.details)

def main():
  options.parse_command_line()
  rank()

if __name__ == '__main__':
  main()
