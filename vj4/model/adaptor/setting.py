import collections
import functools
import itertools

from vj4.model import builtin
from vj4.model import user

Setting = functools.partial(
  collections.namedtuple('Setting', ['family', 'key', 'factory', 'range', 'ui']),
  range=None, ui='input')

PRIVACY_RANGE = collections.OrderedDict(
  [(-1, 'visible_all'), (0, 'visible_user'), (2, 'invisible')])

# Setting keys should not duplicate with user keys or session keys.
SETTINGS = [
  Setting('info', 'gravatar', str),
  Setting('info', 'qq', str),
  Setting('info', 'gender', int, range=builtin.USER_GENDERS),
  Setting('info', 'signature', str, ui='textarea'),
  Setting('privacy', 'show_mail', int, range=PRIVACY_RANGE, ui='option'),
  Setting('privacy', 'show_qq', int, range=PRIVACY_RANGE, ui='option'),
  Setting('preference', 'view_lang', str, range=['zh_CN', 'en'], ui='option'),
  Setting('preference', 'code_lang', str, range=builtin.LANGS, ui='option'),
  Setting('preference', 'show_tags', int),
  Setting('preference', 'send_code', int)]

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
