import collections
import functools
import pytz

from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import user
from vj4.model.adaptor import defaults
from vj4.util import options
from vj4.util import locale

Setting = functools.partial(
    collections.namedtuple('Setting',
                           ['family', 'key', 'factory', 'range', 'default', 'ui', 'name', 'desc']),
    range=None, default=None, ui='text', name='', desc='')

# Setting keys should not duplicate with user keys or session keys.
PREFERENCE_SETTINGS = [
    Setting('setting_display', 'view_lang', str, range=locale.VIEW_LANGS,
            default=options.default_locale, ui='select', name='UI Language'),
    Setting('setting_display', 'timezone', str,
            range=collections.OrderedDict(zip(pytz.common_timezones, pytz.common_timezones)),
            default='Asia/Shanghai', ui='select', name='Timezone'),
    Setting('setting_usage', 'send_code', int, range=constant.setting.FUNCTION_RANGE,
            ui='select', name='Send Code after acceptance',
            desc='If enabled, source code will be emailed to you after the submission is accepted.'),
    Setting('setting_usage', 'code_lang', str, range=constant.language.LANG_TEXTS,
            ui='select', name='Default Code Language'),
    Setting('setting_usage', 'code_template', str,
            ui='textarea', name='Default Code Template',
            desc='If left blank, the built-in template of the corresponding language will be used.')]

ACCOUNT_SETTINGS = [
    Setting('setting_info', 'background_img', int, range=constant.setting.BACKGROUND_RANGE,
            ui='select', name='Background Image'),
    Setting('setting_info', 'gravatar', str,
            name='Gravatar Email', desc='We use Gravatar to present your avatar icon.'),
    Setting('setting_info', 'qq', str,
            name='QQ'),
    Setting('setting_info', 'wechat', str,
            name='WeChat'),
    Setting('setting_info', 'gender', int, range=constant.model.USER_GENDER_RANGE,
            ui='select', name='Gender'),
    Setting('setting_info', 'bio', str,
            ui='markdown', name='Bio'),
    Setting('setting_privacy', 'show_mail', int, range=constant.setting.PRIVACY_RANGE,
            ui='select', name='Email Visibility'),
    Setting('setting_privacy', 'show_qq', int, range=constant.setting.PRIVACY_RANGE,
            ui='select', name='QQ Visibility'),
    Setting('setting_privacy', 'show_wechat', int, range=constant.setting.PRIVACY_RANGE,
            ui='select', name='WeChat Visibility'),
    Setting('setting_privacy', 'show_gender', int, range=constant.setting.PRIVACY_RANGE,
            ui='select', name='Gender Visibility'),
    Setting('setting_privacy', 'show_bio', int, range=constant.setting.PRIVACY_RANGE,
            ui='select', name='Bio Visibility'),
    Setting('setting_privacy', 'show_submission_code', int, range=constant.setting.PRIVACY_RANGE,
            ui='select', name='Submission Code Visibility', default=constant.setting.PRIVACY_SECRET,
            desc='Sets whether your source code is public to others. This option may be overridden by submission options.')]

SETTINGS = PREFERENCE_SETTINGS + ACCOUNT_SETTINGS
SETTINGS_BY_KEY = collections.OrderedDict(zip((s.key for s in SETTINGS), SETTINGS))


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

  def get_code_template(self):
    code_template = self.get_setting('code_template')
    if code_template:
      return code_template
    code_lang = self.get_setting('code_lang')
    if code_lang in defaults.DEFAULT_CODE_TEMPLATES:
      return defaults.DEFAULT_CODE_TEMPLATES[code_lang].strip()
    else:
      return ''


class UserSetting(SettingMixin):
  def __init__(self, udoc):
    self.session = None
    self.user = udoc

  def has_priv(self, p):
    return True
