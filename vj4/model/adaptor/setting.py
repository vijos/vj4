import collections
import functools
import itertools

from vj4 import constant
from vj4.model import builtin
from vj4.model import user

Setting = functools.partial(
  collections.namedtuple('Setting', ['family', 'key', 'factory', 'range', 'ui']),
  range=None, ui='input')

# Setting keys should not duplicate with user keys or session keys.
SETTINGS = [
  Setting('info', 'gravatar', str),
  Setting('info', 'qq', str),
  Setting('info', 'gender', int, range=constant.model.USER_GENDER_RANGE, ui='select'),
  Setting('privacy', 'show_mail', int, range=constant.setting.PRIVACY_RANGE, ui='select'),
  Setting('privacy', 'show_qq', int, range=constant.setting.PRIVACY_RANGE, ui='select'),
  Setting('privacy', 'show_gender', int, range=constant.setting.PRIVACY_RANGE, ui='select'),
  Setting('preference', 'view_lang', str, range=builtin.VIEW_LANGS, ui='select'),
  Setting('preference', 'code_lang', str, range=constant.language.LANG_TEXTS, ui='select'),
  Setting('preference', 'show_tags', int, range=constant.setting.SHOW_TAGS_RANGE, ui='select'),
  Setting('function', 'send_code', int, range=constant.setting.FUNCTION_RANGE, ui='select')]

SETTINGS_BY_KEY = collections.OrderedDict(zip((s.key for s in SETTINGS), SETTINGS))
SETTINGS_BY_FAMILY = collections.OrderedDict(
  (f, list(l)) for f, l in itertools.groupby(SETTINGS, lambda s: s.family))


class SettingMixin(object):
  def get_setting(self, key):
    if self.has_priv(builtin.PRIV_USER_PROFILE) and key in self.user:
      return self.user[key]
    if self.session and key in self.session:
      return self.session[key]
    setting = SETTINGS_BY_KEY[key]
    if setting.range:
      return next(iter(setting.range))
    return setting.factory()

  async def set_settings(self, **kwargs):
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      await user.set_by_uid(self.user['_id'], **kwargs)
    else:
      await self.update_session(**kwargs)
