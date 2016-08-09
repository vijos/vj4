from vj4 import app
from vj4 import error
from vj4.handler import base


@app.route('/lang/{lang}', 'language_set')
class LanguageView(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, lang: str):
    if not lang in ['zh_CN', 'en']:
      raise error.ValidationError('lang')
    await self.set_settings(view_lang=lang)
    self.json_or_redirect(self.referer_or_main)

@app.route('/i18n/{s}', 'i18n')
class I18nView(base.Handler):
  @base.route_argument
  @base.sanitize
  async def get(self, *, s: str):
    self.json(self.translate(s))
