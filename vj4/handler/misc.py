from vj4 import app
from vj4.util import pagination
from vj4.model import domain
from vj4.model import user
from vj4.handler import base
from vj4.util import misc


@app.route('/about', 'about', global_route=True)
class AboutHandler(base.Handler):
  async def get(self):
    self.render('about.html')


@app.route('/wiki/help', 'wiki_help', global_route=True)
class AboutHandler(base.Handler):
  async def get(self):
    self.render('wiki_help.html')


@app.route('/preview', 'preview', global_route=True)
class PreviewHandler(base.Handler):
  @base.post_argument
  @base.sanitize
  async def post(self, *, text: str):
    self.response.content_type = 'text/html'
    self.response.text = misc.markdown(text)

async def render_or_json_rank(self, page, ppcount, pcount, pdocs, **kwargs):
  if 'page_title' not in kwargs:
    kwargs['page_title'] = self.translate(self.TITLE)
  if 'path_components' not in kwargs:
    kwargs['path_components'] = self.build_path((self.translate(self.NAME), None))
  if self.prefer_json:
    list_html = self.render_html('partials/rank.html', page=page, ppcount=ppcount,
                                 pcount=pcount, pdocs=pdocs, psdict=psdict)
    path_html = self.render_html('partials/path.html', path_components=kwargs['path_components'])
    self.json({'title': self.render_title(kwargs['page_title']),
               'fragments': [{'html': list_html},
                             {'html': stat_html},
                             {'html': lucky_html},
                             {'html': path_html}]})
  else:
    self.render('rank.html', page=page, ppcount=ppcount, pcount=pcount, pdocs=pdocs, **kwargs)

@app.route('/rank', 'domain_rank', global_route=True)
class RankHandler(base.Handler):
  USERS_PER_PAGE = 100
  @base.get_argument
  @base.sanitize
  async def get(self, *, domain_id: str="system", page: int=1):
    pdocs, ppcount, pcount = await pagination.paginate(domain.get_multi_user(domain_id=domain_id).sort([('rp', -1)]),
                                                       page, self.USERS_PER_PAGE)
    for pdoc in pdocs:
      pdoc['uname'] = await user.get_by_uid(pdoc['uid'])
      pdoc['uname'] = pdoc['uname']['uname']
    await render_or_json_rank(self, domain_id=domain_id, page=page, ppcount=ppcount, pcount=pcount, pdocs=pdocs, page_title="Rank")
