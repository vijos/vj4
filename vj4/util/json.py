import calendar
import datetime
import json

from bson import objectid


class Encoder(json.JSONEncoder):
  item_separator = ','
  key_separator = ':'

  def __init__(self, **kwargs):
    super(Encoder, self).__init__(ensure_ascii=False, **kwargs)

  def default(self, o):
    if type(o) is objectid.ObjectId:
      return str(o)
    if type(o) is datetime.datetime:
      return calendar.timegm(o.utctimetuple()) * 1000
    return super(Encoder, self).default(o)


class EncoderPretty(Encoder):
  item_separator = ', '
  key_separator = ': '

  def __init__(self, **kwargs):
    super(EncoderPretty, self).__init__(indent=2, **kwargs)

  def default(self, o):
    return super(EncoderPretty, self).default(o)


class Decoder(json.JSONDecoder):
  pass


encode = Encoder().encode
encode_pretty = EncoderPretty().encode
decode = Decoder().decode
