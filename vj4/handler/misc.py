from vj4 import app
from vj4 import template
from vj4.handler import base


@app.route('/preview', 'preview')
class PreviewHandler(base.Handler):
  @base.post_argument
  @base.sanitize
  async def post(self, *, text: str):
    self.json({'html': template.markdown(text)})
