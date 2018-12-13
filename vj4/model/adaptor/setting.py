import collections
import functools
import pytz

from vj4 import constant
from vj4 import error
from vj4.model import builtin
from vj4.model import user
from vj4.model import domain
from vj4.model.adaptor import defaults
from vj4.util import options
from vj4.util import locale

Setting = functools.partial(
    collections.namedtuple('Setting',
                           ['family', 'key', 'factory', 'range', 'default', 'ui', 'name', 'desc',
                            'image_class']),
    range=None, default=None, ui='text', name='', desc='', image_class='')

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
    Setting('setting_info', 'gravatar', str,
            name='Gravatar Email',
            desc='We use <a href="https://en.gravatar.com/" target="_blank">Gravatar</a> to present your avatar icon.'),
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
    Setting('setting_customize', 'background_img', int, range=constant.setting.BACKGROUND_RANGE,
            ui='image_radio', name='Profile Background Image',
            desc='Choose the background image in your profile page.',
            image_class='user-profile-bg--thumbnail-{0}')]


DOMAIN_ACCOUNT_SETTINGS = [
    Setting('setting_info_domain', 'display_name', str,
            name='Display Name')]

DOMAIN_SETTINGS_KEYS = set(s.key for s in DOMAIN_ACCOUNT_SETTINGS)

SETTINGS = PREFERENCE_SETTINGS + ACCOUNT_SETTINGS + DOMAIN_ACCOUNT_SETTINGS
SETTINGS_BY_KEY = collections.OrderedDict(zip((s.key for s in SETTINGS), SETTINGS))


class SettingMixin(object):
  def get_setting(self, key):
    if self.has_priv(builtin.PRIV_USER_PROFILE) and key in self.user:
      return self.user[key]
    if self.has_priv(builtin.PRIV_USER_PROFILE) and key in self.domain_user:
      return self.domain_user[key]
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
    user_setting = {}
    domain_user_setting = {}
    domain_user_unset_keys = []
    for key, value in kwargs.items():
      if key not in SETTINGS_BY_KEY:
        raise error.UnknownFieldError(key)
      setting = SETTINGS_BY_KEY[key]
      value = value.strip()
      kwargs[key] = setting.factory(value)
      if setting.range and kwargs[key] not in setting.range:
        raise error.ValidationError(key)

      if key in DOMAIN_SETTINGS_KEYS:
        if value:
          domain_user_setting[key] = kwargs[key]
        else:
          domain_user_unset_keys.append(key)
      else:
        user_setting[key] = kwargs[key]

    if self.has_priv(builtin.PRIV_USER_PROFILE):
      if user_setting:
        await user.set_by_uid(self.user['_id'], **user_setting)
      if domain_user_setting:
        await domain.set_user(domain_id=self.domain_id, uid=self.user['_id'], **domain_user_setting)
      if domain_user_unset_keys:
        await domain.unset_user(self.domain_id, self.user['_id'], domain_user_unset_keys)
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
