from vj4 import app
from vj4.model import builtin
from vj4.model import domain
from vj4.model import user
from vj4.util import pagination
from vj4.handler import base


@app.route('/ranking', 'ranking_main')
class RankingMainHandler(base.Handler):
  USERS_PER_PAGE = 100

  @base.require_priv(builtin.PRIV_USER_PROFILE)
  @base.require_perm(builtin.PERM_VIEW_RANKING)
  @base.get_argument
  @base.route_argument
  @base.sanitize
  async def get(self, *, page: int=1):
    dudocs, dupcount, _ = await pagination.paginate(
        domain.get_multi_user(domain_id=self.domain_id, rp={'$gt': 0.0}).sort([('rank', 1)]),
        page, self.USERS_PER_PAGE)
    udict = await user.get_dict(dudoc['uid'] for dudoc in dudocs)
    self.render('ranking_main.html', page=page, dupcount=dupcount, dudocs=dudocs, udict=udict)
