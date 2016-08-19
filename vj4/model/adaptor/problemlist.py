from vj4.model import document
from vj4.util import argmethod
from vj4.util import validator


@argmethod.wrap
async def add(domain_id: str, title: str, content: str, owner_uid: int,
              lid: document.convert_doc_id = None):
  validator.check_title(title)
  validator.check_content(content)
  return await document.add(domain_id, content, owner_uid,
                            document.TYPE_PROBLEM_LIST, lid, title=title, problem=[])


@argmethod.wrap
async def get(domain_id: str, lid: document.convert_doc_id):
  # TODO(twd2): check if deleted?
  return await document.get(domain_id, document.TYPE_PROBLEM_LIST, lid)


@argmethod.wrap
async def set(domain_id: str, lid: document.convert_doc_id, **kwargs):
  # TODO(twd2): check if deleted?
  if 'title' in kwargs:
    validator.check_title(kwargs['title'])
  if 'content' in kwargs:
    validator.check_content(kwargs['content'])
  return await document.set(domain_id, document.TYPE_PROBLEM_LIST, lid,
                            **kwargs)


@argmethod.wrap
async def delete(domain_id: str, lid: document.convert_doc_id):
  return await document.set(domain_id, document.TYPE_PROBLEM_LIST, lid,
                            deleted=True)


@argmethod.wrap
async def add_problem(domain_id: str, lid: document.convert_doc_id, pid: document.convert_doc_id):
  return await document.add_to_set(domain_id, document.TYPE_PROBLEM_LIST, lid, 'problem', pid)


@argmethod.wrap
async def delete_problem(domain_id: str, lid: document.convert_doc_id,
                         pid: document.convert_doc_id):
  return await document.pull(domain_id, document.TYPE_PROBLEM_LIST, lid, 'problem', [pid])


@argmethod.wrap
async def set_star(domain_id: str, lid: document.convert_doc_id, uid: int, star: bool):
  return await document.set_status(domain_id, document.TYPE_PROBLEM_LIST, lid, uid, star=star)


if __name__ == '__main__':
  argmethod.invoke_by_args()
