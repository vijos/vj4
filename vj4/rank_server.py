import json
import logging
from vj4.util import options
from aiohttp import web
from pymongo import MongoClient

DB_HOST = 'localhost'
DB_PORT = 27017
DB_NAME = 'test'
COLL_NAME = 'user'

CONN = MongoClient(DB_HOST, DB_PORT)
DB = CONN[DB_NAME]
COLL = DB[COLL_NAME]

level_config = None

def load_conf(path):
  global level_config
  with open(path) as f:
    level_config = json.load(f)

def rank_data(udocs):
  global level_config

  stack = list()
  result = list()
  rank = 1
  for udoc in udocs:
    if len(stack) == 0:
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
      # print(perc, key, value)
      return int(key)

async def handle_rank(request):
  udocs = list(COLL.find())
  udocs.sort(key = lambda x:(x['rp']), reverse=True)

  rank_array = rank_data(udocs)
  total = rank_array[-1]

  index = 0
  for udoc in udocs:
    rankN = rank_array[index]
    udoc['rankN'] = rankN
    udoc['level'] = count_level(rankN / total)
    # print((index, udoc['rankN'], udoc['level']))
    COLL.save(udoc)
    index += 1

  response = {
      'status':200,
      'success':True
  }

  return web.Response(
    body=json.dumps(response).encode('utf-8'),
    content_type="application/json",
    charset="utf-8")

options.define('level_config', default='level_config.json', help='Level Config')
options.define('port', default=8887, help='HTTP server port')

_logger = logging.getLogger(__name__)

if __name__ == '__main__':
  options.parse_command_line()

  load_conf(options.options.level_config)

  app = web.Application()
  app.router.add_route('GET', '/api/rank', handle_rank)

  web.run_app(app,
              port=options.options.port,
              print=lambda s: [logging.info(l) for l in s.splitlines()])
