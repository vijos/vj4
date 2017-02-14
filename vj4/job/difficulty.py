import asyncio
import logging
import math

from vj4 import db
from vj4.model import builtin
from vj4.model import domain
from vj4.model import document
from vj4.model.adaptor import problem
from vj4.util import argmethod
from vj4.util import domainjob


_logger = logging.getLogger(__name__)


_CACHE_INFO = {
  'last_s': 0.0,
  'last_y': 0,
  'values': [0.0]
}


@argmethod.wrap
def _LOGP(x: float):
  sqrt_2_pi = 2.506628274631000502415765284811 # math.sqrt(2 * math.pi)
  return math.exp(-1.0 * pow(math.log(x, math.e), 2) / 0.5) / x / 0.5 / sqrt_2_pi


@argmethod.wrap
def _integrate_ensure_cache(y: int):
  last_y = _CACHE_INFO['last_y']
  if y <= last_y:
    return _CACHE_INFO
  s = _CACHE_INFO['last_s']
  dx = 0.1
  dT = 2
  x0 = last_y / dT * dx
  while y > last_y:
    x0 += dx
    s += _LOGP(x0) * dx
    for i in range(dT):
      _CACHE_INFO['values'].append(s)
    last_y += dT
  _CACHE_INFO['last_y'] = last_y
  _CACHE_INFO['last_s'] = s
  return _CACHE_INFO


_integrate_ensure_cache(1000000)


@argmethod.wrap
def _integrate_direct(y: int):
  last_y = 0
  s = 0.0
  dx = 0.1
  dT = 2
  x0 = last_y / dT * dx
  while y > last_y:
    x0 += dx
    s += _LOGP(x0) * dx
    last_y += dT
  return s


@argmethod.wrap
def _integrate(y: int):
  _integrate_ensure_cache(y)
  return _CACHE_INFO['values'][y]


@argmethod.wrap
def difficulty_altorithm(num_submit: int, num_accept: int):
  """Algorithm is written by doc."""
  if not num_submit:
    return None

  s = _integrate(num_submit)
  ac_rate = num_accept / num_submit
  ans = int(10.0 - 1.30 * s * 10.0 * ac_rate)
  if ans <= 0:
    ans = 1
  return ans


def _get_difficulty(pdoc, calculated_difficulty):
  # allow admin set difficulty
  setting = pdoc.get('difficulty_setting', next(iter(problem.SETTING_DIFFICULTY_RANGE)))
  if setting == problem.SETTING_DIFFICULTY_ALGORITHM:
    return calculated_difficulty
  elif setting == problem.SETTING_DIFFICULTY_ADMIN:
     return pdoc['difficulty_admin']
  elif setting == problem.SETTING_DIFFICULTY_AVERAGE \
       and pdoc.get('difficulty_admin', None):
       return int(round((calculated_difficulty + pdoc['difficulty_admin']) / 2))
  else:
    return calculated_difficulty


@argmethod.wrap
async def update_problem(domain_id: str, pid: document.convert_doc_id):
  pdoc = await problem.get(domain_id, pid)
  difficulty_algo = difficulty_altorithm(pdoc['num_submit'], pdoc['num_accept'])
  difficulty = _get_difficulty(pdoc, difficulty_algo)
  return await problem.edit(domain_id, pdoc['doc_id'], difficulty=difficulty,
                            difficulty_algo=difficulty_algo)


@domainjob.wrap
async def recalc(domain_id: str):
  pdocs = problem.get_multi(domain_id=domain_id,
                            fields={'_id': 1, 'doc_id': 1, 'num_accept': 1, 'num_submit': 1})
  coll = db.Collection('document')
  bulk = coll.initialize_unordered_bulk_op()
  execute = False
  _logger.info('Calculating')
  async for pdoc in pdocs:
    difficulty_algo = difficulty_altorithm(pdoc['num_submit'], pdoc['num_accept'])
    difficulty = _get_difficulty(pdoc, difficulty_algo)
    bulk.find({'_id': pdoc['_id']}) \
        .update_one({'$set': {'difficulty': difficulty,
                              'difficulty_algo': difficulty_algo}})
    execute = True
  if execute:
    _logger.info('Committing')
    await bulk.execute()
  

if __name__ == '__main__':
  argmethod.invoke_by_args()
