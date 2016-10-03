from vj4 import app
from vj4 import template
from vj4.handler import base


@app.route('/about', 'about')
class AboutHandler(base.Handler):
  async def get(self):
    self.render('about.html')


@app.route('/wiki/help', 'wiki_help')
class AboutHandler(base.Handler):
  async def get(self):
    self.render('wiki_help.html')


@app.route('/preview', 'preview')
class PreviewHandler(base.Handler):
  @base.post_argument
  @base.sanitize
  async def post(self, *, text: str):
    self.response.content_type = 'text/html'
    self.response.text = template.markdown(text)
