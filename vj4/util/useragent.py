import httpagentparser

_PLATFORM_ICON_MAP = {
  'windows': 'windows',
  'linux': 'linux',
  'mac os': 'mac',
  'macintosh': 'mac',
  'ios': 'ios',
  'chromeos': 'chromeos',
  'android': 'android',
  'playstation': 'unknown',
  'blackberry': 'mobile',
  'symbian': 'mobile',
  'nokia s40': 'mobile',
}


def parse(ua: str):
  dresult = httpagentparser.detect(ua)
  platform = 'unknown'
  if 'platform' in dresult and dresult['platform']['name'] != None:
    platform = dresult['platform']['name']
  elif 'os' in dresult and dresult['os']['name'] != None:
    platform = dresult['os']['name']
  icon = _PLATFORM_ICON_MAP.get(platform.strip().lower(), 'unknown')
  os, browser = httpagentparser.simple_detect(ua)
  if (ua.lower().find('amd64') >= 0 or ua.lower().find('x86_64') >= 0 or
      ua.lower().find('x64') >= 0):
    os += ' x64'
  return {
    'str': ua,
    'icon': icon,
    'os': os,
    'browser': browser,
  }
