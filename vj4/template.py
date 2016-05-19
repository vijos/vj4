import hashlib
import hoedown
import jinja2
import markupsafe
import vj4
import math
from jinja2 import ext
from os import path
from urllib import parse
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
    self.globals['pager'] = pager

    self.filters['markdown'] = markdown
    self.filters['json'] = json.encode
    self.filters['gravatar_url'] = gravatar_url
    self.filters['pager_link'] = pager_link

MARKDOWN_EXTENSIONS = (hoedown.EXT_TABLES |            # Parse PHP-Markdown style tables.
                       hoedown.EXT_FENCED_CODE |       # Parse fenced code blocks.
                       hoedown.EXT_AUTOLINK |          # Automatically turn safe URLs into links.
                       hoedown.EXT_NO_INTRA_EMPHASIS)  # Disable emphasis_between_words.
MARKDOWN_RENDER_FLAGS = (hoedown.HTML_ESCAPE |         # Escape all HTML.
                         hoedown.HTML_HARD_WRAP)       # Render each linebreak as <br>.

def markdown(text):
  return markupsafe.Markup(
      hoedown.html(text, extensions=MARKDOWN_EXTENSIONS, render_flags=MARKDOWN_RENDER_FLAGS))

def gravatar_url(gravatar, size=200):
  # TODO: 'd' should be https://domain/img/avatar.png
  if gravatar:
    gravatar_hash = hashlib.md5(gravatar.lower().encode()).hexdigest()
  else:
    gravatar_hash = ''
  return ('https://www.gravatar.com/avatar/' + gravatar_hash + "?" +
          parse.urlencode({'d': 'mm', 's': str(size)}))

def pager_link(href_pattern, page):
  return href_pattern.replace('{page}', str(page))

def pager(count, num_per_page, current_page1 = 1):
  pager_radius = 2
  max_pages = math.ceil(count / num_per_page)
  if max_pages == 0:
    return []
  if current_page1 <= 1:
    current_page1 = 1
  if current_page1 > max_pages:
    current_page1 = max_pages
  pager_first = current_page1 - pager_radius
  pager_last = current_page1 + pager_radius

  # adjust range
  i = pager_first
  if pager_last > max_pages:
    i += max_pages - pager_last
    pager_last = max_pages
  if i < 1:
    pager_last += 1 - i
    i = 1

  # generate pagination list
  data = []
  if current_page1 > 1:
    data.append({'page': 1, 'text': 'pager_first', 'type': 'first'})
    data.append({'page': current_page1 - 1, 'text': 'pager_previous', 'type': 'previous'})
  if i != max_pages:
    if i > 1:
      data.append({'page': -1, 'text': '...', 'type': 'ellipsis'})
    while i <= pager_last and i <= max_pages:
      if i == current_page1:
        data.append({'page': i, 'text': str(i), 'type': 'current'})
      else:
        data.append({'page': i, 'text': str(i), 'type': 'page'})
      i += 1
    if i < max_pages:
      data.append({'page': -1, 'text': '...', 'type': 'ellipsis'})
  if current_page1 < max_pages:
    data.append({'page': current_page1 + 1, 'text': 'pager_next', 'type': 'next'})
    data.append({'page': max_pages, 'text': 'pager_last', 'type': 'last'})

  return data
