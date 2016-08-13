import hashlib
import hoedown
from os import path
from urllib import parse

import jinja2
import markupsafe
from jinja2 import ext

import vj4
import vj4.constant
from vj4.util import json
from vj4.util import options

class Environment(jinja2.Environment):
  def __init__(self):
    super(Environment, self).__init__(
      loader=jinja2.FileSystemLoader(path.join(path.dirname(__file__), 'ui/templates')),
      extensions=[ext.with_],
      auto_reload=options.options.debug,
      autoescape=True,
      trim_blocks=True)
    globals()[self.__class__.__name__] = lambda: self  # singleton

    self.globals['vj4'] = vj4
    self.globals['static_url'] = lambda s: options.options.cdn_prefix + s
    self.globals['paginate'] = paginate

    self.filters['markdown'] = markdown
    self.filters['json'] = json.encode
    self.filters['gravatar_url'] = gravatar_url


MARKDOWN_EXTENSIONS = (hoedown.EXT_TABLES |  # Parse PHP-Markdown style tables.
                       hoedown.EXT_FENCED_CODE |  # Parse fenced code blocks.
                       hoedown.EXT_AUTOLINK |  # Automatically turn safe URLs into links.
                       hoedown.EXT_NO_INTRA_EMPHASIS)  # Disable emphasis_between_words.
MARKDOWN_RENDER_FLAGS = (hoedown.HTML_ESCAPE |  # Escape all HTML.
                         hoedown.HTML_HARD_WRAP)  # Render each linebreak as <br>.


def markdown(text):
  return markupsafe.Markup(
    hoedown.html(text, extensions=MARKDOWN_EXTENSIONS, render_flags=MARKDOWN_RENDER_FLAGS))


def gravatar_url(gravatar, size=200):
  if gravatar:
    gravatar_hash = hashlib.md5(gravatar.lower().encode()).hexdigest()
    return ('//gravatar.lug.ustc.edu.cn/avatar/' + gravatar_hash + "?" +
            parse.urlencode({'d': options.options.url_prefix + '/img/avatar.png', 's': str(size)}))
  else:
    return options.options.url_prefix + '/img/avatar.png'


def paginate(page, num_pages):
  radius = 2
  if page > 1:
    yield 'first', 1
    yield 'previous', page - 1
  if page <= radius:
    first, last = 1, min(1 + radius * 2, num_pages)
  elif page >= num_pages - radius:
    first, last = max(1, num_pages - radius * 2), num_pages
  else:
    first, last = page - radius, page + radius
  if first > 1:
    yield 'ellipsis', 0
  for page0 in range(first, last + 1):
    if page0 != page:
      yield 'page', page0
    else:
      yield 'current', page
  if last < num_pages:
    yield 'ellipsis', 0
  if page < num_pages:
    yield 'next', page + 1
    yield 'last', num_pages
