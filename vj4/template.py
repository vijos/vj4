import hashlib
import hoedown
import jinja2
import markupsafe
import vj4
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
    self.filters['markdown'] = markdown

    self.filters['json'] = json.encode
    self.filters['gravatar_url'] = gravatar_url

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
