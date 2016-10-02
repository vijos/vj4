def ranked(diter, equ_func=lambda a, b: a == b):
  last_doc = None
  r = 0
  count = 0
  for doc in diter:
    count += 1
    if count == 1 or not equ_func(last_doc, doc):
      r = count
    last_doc = doc
    yield (r, doc)


if __name__ == '__main__':
  for r, v in ranked(sorted([1, 2, 2, 2, 2, 3, 3, 3, 4, 5, 6])):
    print(r, v)
