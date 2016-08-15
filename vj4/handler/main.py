from vj4 import app
from vj4.model.adaptor import discussion
from vj4.handler import base


@app.route('/', 'main')
class MainHandler(base.Handler):
  async def get(self):
    self.render('main.html',
                discussion_nodes=await discussion.get_nodes(self.domain_id),
                path_components=[(self.domain_id, None)])


@app.route('/500', 'error')
class ErrorHandler(base.Handler):
  async def get(self):
    raise Exception('swx template')
