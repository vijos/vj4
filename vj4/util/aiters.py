"""Utility functions for asynchronous iterators."""
async def to_dict(aiter, key_field_name):
  result = dict()
  async for doc in aiter:
    result[doc[key_field_name]] = doc
  return result
