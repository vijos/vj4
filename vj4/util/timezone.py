import pytz

def ensure_tzinfo(t):
  if not t.tzinfo:
    return t.replace(tzinfo=pytz.utc)
  return t
