import calendar
import datetime
import json

from bson import objectid


class Encoder(json.JSONEncoder):
  item_separator = ','
  key_separator = ':'

  def __init__(self):
    super(Encoder, self).__init__(ensure_ascii=False)

  def default(self, o):
    if type(o) is objectid.ObjectId:
      return str(o)
    if type(o) is datetime.datetime:
      return calendar.timegm(o.utctimetuple()) * 1000
    return super(Encoder, self).default(o)


class Decoder(json.JSONDecoder):
  pass


encode = Encoder().encode
decode = Decoder().decode
