from vj4 import app
from vj4 import template
from vj4.handler import base
from vj4.util import template_func


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
    self.response.text = template_func.markdown(text)
