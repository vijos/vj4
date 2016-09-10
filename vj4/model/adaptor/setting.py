import collections
import functools
import itertools

from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import user
from vj4.util import options
from vj4.util import locale

Setting = functools.partial(
  collections.namedtuple('Setting', ['category', 'family', 'key', 'factory', 'range', 'default',
                                     'ui', 'name', 'desc']),
  range=None, default=None, ui='text', name='', desc='')

# Setting keys should not duplicate with user keys or session keys.
SETTINGS = [
  Setting('preference', 'setting_display', 'view_lang', str, range=locale.VIEW_LANGS,
          default=options.options.default_locale, ui='select', name='UI Language'),
  Setting('preference', 'setting_display', 'timezone', str, range=builtin.TIMEZONES,
          default='Asia/Shanghai', ui='select', name='Timezone'),
  Setting('preference', 'setting_display', 'show_tags', int, range=constant.setting.SHOW_TAGS_RANGE,
          ui='select', name='Problem Tags Visibility',
          desc='Whether to show tags in the problem list.'),
  Setting('preference', 'setting_usage', 'send_code', int, range=constant.setting.FUNCTION_RANGE,
          ui='select', name='Send Code after acceptance',
          desc='If enabled, source code will be emailed to you after the submission is accepted.'),
  Setting('preference', 'setting_usage', 'code_lang', str, range=constant.language.LANG_TEXTS,
          ui='select', name='Default Code Language'),
  Setting('preference', 'setting_usage', 'code_template', str,
          ui='textarea', name='Default Code Template',
          desc='If left blank, the built-in template of the corresponding language will be used.'),
  Setting('account', 'setting_info', 'gravatar', str,
          name='Gravatar Email',
          desc='We use Gravatar to present your avatar icon.'),
  Setting('account', 'setting_info', 'qq', str,
          name='QQ'),
  Setting('account', 'setting_info', 'gender', int, range=constant.model.USER_GENDER_RANGE,
          ui='select', name='Gender'),
  Setting('account', 'setting_privacy', 'show_mail', int, range=constant.setting.PRIVACY_RANGE,
          ui='select', name='Email Visibility'),
  Setting('account', 'setting_privacy', 'show_qq', int, range=constant.setting.PRIVACY_RANGE,
          ui='select', name='QQ Visibility'),
  Setting('account', 'setting_privacy', 'show_gender', int, range=constant.setting.PRIVACY_RANGE,
          ui='select', name='Gender Visibility')]

SETTINGS_BY_KEY = collections.OrderedDict(zip((s.key for s in SETTINGS), SETTINGS))
SETTINGS_BY_CATEGORY = collections.OrderedDict(
  (f, list(l)) for f, l in itertools.groupby(SETTINGS, lambda s: s.category))


class SettingMixin(object):

  def get_setting(self, key):
    if self.has_priv(builtin.PRIV_USER_PROFILE) and key in self.user:
      return self.user[key]
    if self.session and key in self.session:
      return self.session[key]
    setting = SETTINGS_BY_KEY[key]
    if setting.default:
      assert not setting.range or setting.default in setting.range
      return setting.default
    if setting.range:
      return next(iter(setting.range))
    return setting.factory()

  async def set_settings(self, **kwargs):
    for key, value in kwargs.items():
      if key not in SETTINGS_BY_KEY:
        raise error.UnknownFieldError(key)
      setting = SETTINGS_BY_KEY[key]
      kwargs[key] = setting.factory(value)
      if setting.range and kwargs[key] not in setting.range:
        raise error.ValidationError(key)
    if self.has_priv(builtin.PRIV_USER_PROFILE):
      await user.set_by_uid(self.user['_id'], **kwargs)
    else:
      await self.update_session(**kwargs)
