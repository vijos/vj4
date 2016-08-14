
"""
!!! WARNING !!!
This file is auto-generated from `vj4/constant/record.js`.
Don't edit directly, otherwise it will be overwritten.
Run `npm run generate:constant` to update this file.
"""

import collections

STATUS_WAITING = 0

STATUS_ACCEPTED = 1

STATUS_WRONG_ANSWER = 2

STATUS_TIME_LIMIT_EXCEEDED = 3

STATUS_MEMORY_LIMIT_EXCEEDED = 4

STATUS_OUTPUT_LIMIT_EXCEEDED = 5

STATUS_RUNTIME_ERROR = 6

STATUS_COMPILE_ERROR = 7

STATUS_SYSTEM_ERROR = 8

STATUS_CANCELED = 9

STATUS_ETC = 10

STATUS_JUDGING = 20

STATUS_COMPILING = 21

STATUS_IGNORED = 30

TYPE_SUBMISSION = 0

TYPE_PRETEST = 1

STATUS_TEXTS = collections.OrderedDict([
(0, "Waiting"),
(1, "Accepted"),
(2, "Wrong Answer"),
(3, "Time Exceeded"),
(4, "Memory Exceeded"),
(5, "Output Exceeded"),
(6, "Runtime Error"),
(7, "Compile Error"),
(8, "System Error"),
(9, "Cancelled"),
(10, "Unknown Error"),
(20, "Running"),
(21, "Compiling"),
(30, "Ignored"),
])

STATUS_ABBRS = collections.OrderedDict([
(0, ""),
(1, "AC"),
(2, "WA"),
(3, "TLE"),
(4, "MLE"),
(5, "OLE"),
(6, "RE"),
(7, "CE"),
(8, "SE"),
(9, "ETC"),
(10, "ETC"),
(20, "ETC"),
(21, "ETC"),
(30, "ETC"),
])

STATUS_CODES = collections.OrderedDict([
(0, "pending"),
(1, "pass"),
(2, "fail"),
(3, "fail"),
(4, "fail"),
(5, "fail"),
(6, "fail"),
(7, "fail"),
(8, "fail"),
(9, "ignored"),
(10, "fail"),
(20, "progress"),
(21, "progress"),
(30, "ignored"),
])

TYPE_TEXTS = collections.OrderedDict([
(0, "Submission"),
(1, "Pretest"),
])

