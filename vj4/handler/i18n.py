from vj4 import app
from vj4.handler import base


@app.route('/lang/{lang}', 'language_set', global_route=True)
class LanguageHandler(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, lang: str):
    await self.set_settings(view_lang=lang)
    self.json_or_redirect(self.referer_or_main)
