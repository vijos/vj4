import hashlib
import hoedown
import re
from os import path
from urllib import parse

import jinja2
import jinja2.ext
import jinja2.runtime
import markupsafe

import vj4
import vj4.constant
import vj4.job
from vj4.service import staticmanifest
from vj4.util import json
from vj4.util import options


class Undefined(jinja2.runtime.Undefined):
  def __getitem__(self, _):
    return self

  if options.debug:
    __str__ = jinja2.runtime.Undefined.__call__


class Environment(jinja2.Environment):
  def __init__(self):
    super(Environment, self).__init__(
        loader=jinja2.FileSystemLoader(path.join(path.dirname(__file__), 'ui/templates')),
        extensions=[jinja2.ext.with_],
        auto_reload=options.debug,
        autoescape=True,
        trim_blocks=True,
        undefined=Undefined)
    globals()[self.__class__.__name__] = lambda: self  # singleton

    self.globals['vj4'] = vj4
    self.globals['static_url'] = lambda s: options.cdn_prefix + staticmanifest.get(s)
    self.globals['paginate'] = paginate

    self.filters['markdown'] = markdown
    self.filters['json'] = json.encode
    self.filters['gravatar_url'] = gravatar_url
    self.filters['format_size'] = format_size



MARKDOWN_EXTENSIONS = (hoedown.EXT_TABLES |  # Parse PHP-Markdown style tables.
                       hoedown.EXT_FENCED_CODE |  # Parse fenced code blocks.
                       hoedown.EXT_AUTOLINK |  # Automatically turn safe URLs into links.
                       hoedown.EXT_NO_INTRA_EMPHASIS |  # Disable emphasis_between_words.
                       hoedown.EXT_MATH |  # Parse TeX $$math$$ syntax, Kramdown style.
                       hoedown.EXT_SPACE_HEADERS |  # Require a space after '#' in headers.
                       hoedown.EXT_MATH_EXPLICIT |  # Instead of guessing by context, parse $inline math$ and $$always block math$$ (requires EXT_MATH).
                       hoedown.EXT_DISABLE_INDENTED_CODE)  # Don't parse indented code blocks.
MARKDOWN_RENDER_FLAGS = (hoedown.HTML_ESCAPE |  # Escape all HTML.
                         hoedown.HTML_HARD_WRAP)  # Render each linebreak as <br>.


FS_RE = re.compile(r'\(vijos\:\/\/fs\/([0-9a-f]{40,})\)')


def fs_replace(m):
  # TODO(twd2): reverse_url
  return '(' + options.cdn_prefix.rstrip('/') + '/fs/' + m.group(1) + ')'


def markdown(text):
  text = FS_RE.sub(fs_replace, text)
  return markupsafe.Markup(hoedown.html(
      text, extensions=MARKDOWN_EXTENSIONS, render_flags=MARKDOWN_RENDER_FLAGS))


def gravatar_url(gravatar, size=200):
  # TODO: 'd' should be https://domain/img/avatar.png
  if gravatar:
    gravatar_hash = hashlib.md5(gravatar.lower().encode()).hexdigest()
  else:
    gravatar_hash = ''
  return ('//gravatar.proxy.ustclug.org/avatar/' + gravatar_hash + "?" +
          parse.urlencode({'d': 'mm', 's': str(size)}))


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


def format_size(size, base=1, ndigits=3):
  size *= base
  unit = 1024
  unit_names = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']
  for unit_name in unit_names:
    if size < unit:
      return '{0}{1}'.format(round(size, ndigits=ndigits), unit_name)
    size /= unit
  return '{0}{1}'.format(round(size * unit, ndigits=ndigits), unit_names[-1])
