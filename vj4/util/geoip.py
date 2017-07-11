import geoip2.database
import os.path

_GEOIP2_DB_FILE = './GeoLite2-City.mmdb'

if os.path.isfile(_GEOIP2_DB_FILE):
  _reader = geoip2.database.Reader(_GEOIP2_DB_FILE)
else:
  _reader = None

_LOCALE_MAP = {
  'zh_CN': 'zh-CN'
}


def ip2geo(ip: str, locale: str='en'):
  if _reader == None:
    return 'Not available'

  # Map VJ locale string to MaxMind locale string
  locale = _LOCALE_MAP.get(locale, locale)

  try:
    geodoc = _reader.city(ip)
    geo = []

    if locale in geodoc.city.names:
      geo.append(geodoc.city.names[locale])
    elif 'en' in geodoc.city.names:
      geo.append(geodoc.city.names['en'])

    if locale in geodoc.country.names:
      geo.append(geodoc.country.names[locale])
    elif 'en' in geodoc.country.names:
      geo.append(geodoc.country.names['en'])

    if len(geo) == 0:
      return 'Unknown'
    else:
      return ', '.join(geo)
  except geoip2.errors.AddressNotFoundError:
    return 'Unknown'
