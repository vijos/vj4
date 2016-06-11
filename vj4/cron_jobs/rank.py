from pymongo import MongoClient
from pymongo.errors import BulkWriteError

DB_HOST = 'localhost'
DB_PORT = 27017
DB_NAME = 'test'
COLL_NAME = 'user'

CONN = MongoClient(DB_HOST, DB_PORT)
DB = CONN[DB_NAME]
COLL = DB[COLL_NAME]

# Key represents level
# Value represents percent
# E.g. "10": 1 means that people who rank in 1% will get 10 levels
level_config = {
    "10": 1,
    "9": 2,
    "8": 3,
    "7": 5,
    "6": 10,
    "5": 20,
    "4": 30,
    "3": 50,
    "2": 80,
    "1": 100
}

def rank_data(udocs):
  global level_config

  stack = list()
  result = list()
  rank = 1
  for udoc in udocs:
    if not stack:
      stack.append(udoc)
    elif udoc['rp'] == stack[-1]['rp']:
      stack.append(udoc)
    else:
      while len(stack) != 0:
        doc = stack.pop()
        result.append(rank)
      rank += 1
      stack.append(udoc)

  while len(stack) != 0:
    doc = stack.pop()
    result.append(rank)

  return result

def count_level(perc):
  global level_config

  perc *= 100

  for key, value in level_config.items():
    if perc <= value:
      return int(key)

def handle_rank():
  udocs = list(COLL.find())
  udocs.sort(key = lambda x:(x['rp']), reverse=True)

  rank_array = rank_data(udocs)
  total = rank_array[-1]

  index = 0
  bulk = COLL.initialize_unordered_bulk_op()

  for udoc in udocs:
    rankN = rank_array[index]
    level = count_level(rankN / total)
    bulk.find({'_id':udoc['_id']}).update_one(
      {'$set':
        {
          'rankN':rankN,
          'level':level
          }})
    index += 1

  try:
    bulk.execute()
  except BulkWriteError as bwe:
    pprint(bwe.details)

def main():
  handle_rank()

if __name__ == '__main__':
  main()
