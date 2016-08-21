"""Utility functions for asynchronous iterators."""
async def to_dict(aiter, field):
  result = dict()
  async for doc in aiter:
    result[doc[field]] = doc
  return result


async def to_dict_multi(aiter, *fields):
  result = dict()
  async for doc in aiter:
    result[tuple(doc[field] for field in fields)] = doc
  return result
