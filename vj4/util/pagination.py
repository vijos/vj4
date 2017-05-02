import asyncio
from vj4 import error


async def paginate(cursor, page: int, page_size: int):
  if page <= 0:
    raise error.ValidationError('page')
  count, page_docs = await asyncio.gather(cursor.count(),
                                          cursor.skip((page - 1) * page_size) \
                                                .limit(page_size) \
                                                .to_list())
  num_pages = (count + page_size - 1) // page_size
  return page_docs, num_pages, count
