import collections
import datetime
import pytz

from vj4 import constant
from vj4.util import version

# Permissions.
# Domain settings.
PERM_NONE = 0
PERM_VIEW = 1 << 0
PERM_SET_PERM = 1 << 1
PERM_MOD_BADGE = 1 << 2
PERM_EDIT_DESCRIPTION = 1 << 3
PERM_TRANSFER = -1

# Problem and Record.
PERM_CREATE_PROBLEM = 1 << 4
PERM_EDIT_PROBLEM = 1 << 5
PERM_VIEW_PROBLEM = 1 << 6
PERM_SUBMIT_PROBLEM = 1 << 7
PERM_READ_PROBLEM_DATA = 1 << 8
PERM_REJUDGE_PROBLEM = 1 << 9
PERM_REJUDGE = 1 << 10

# Problem Solution.
PERM_VIEW_PROBLEM_SOLUTION = 1 << 11
PERM_CREATE_PROBLEM_SOLUTION = 1 << 12
PERM_VOTE_PROBLEM_SOLUTION = 1 << 13
PERM_EDIT_PROBLEM_SOLUTION = 1 << 14
PERM_DELETE_PROBLEM_SOLUTION = 1 << 15
PERM_REPLY_PROBLEM_SOLUTION = 1 << 16
PERM_EDIT_PROBLEM_SOLUTION_REPLY = 1 << 17
PERM_DELETE_PROBLEM_SOLUTION_REPLY = 1 << 18

# Discussion.
PERM_VIEW_DISCUSSION = 1 << 19
PERM_CREATE_DISCUSSION = 1 << 20
PERM_EDIT_DISCUSSION = 1 << 21
PERM_DELETE_DISCUSSION = 1 << 22
PERM_REPLY_DISCUSSION = 1 << 23
PERM_EDIT_DISCUSSION_REPLY = 1 << 24
PERM_DELETE_DISCUSSION_REPLY = 1 << 25

# Contest.
PERM_VIEW_CONTEST = 1 << 26
PERM_VIEW_CONTEST_STATUS = 1 << 27
PERM_VIEW_CONTEST_HIDDEN_STATUS = 1 << 28
PERM_CREATE_CONTEST = 1 << 29
PERM_ATTEND_CONTEST = 1 << 30

# Training.
PERM_VIEW_TRAINING = 1 << 31

PERM_ALL = -1

# Privileges.
PRIV_NONE = 0
PRIV_SET_PRIV = 1 << 0
PRIV_SET_PERM = 1 << 1
PRIV_USER_PROFILE = 1 << 2
PRIV_REGISTER_USER = 1 << 3
PRIV_READ_RECORD_CODE = 1 << 4
PRIV_READ_PROBLEM_DATA = 1 << 5
PRIV_READ_PRETEST_DATA = 1 << 6
PRIV_WRITE_RECORD = 1 << 7
PRIV_VIEW_ALL_DOMAIN = 1 << 8
PRIV_CREATE_DOMAIN = 1 << 9
PRIV_ALL = -1

# Roles.
ROLE_DEFAULT = 'default'
ROLE_ADMIN = 'admin'

# Domains.
DOMAIN_ID_SYSTEM = 'system'
DEFAULT_PERMISSIONS = (PERM_VIEW |
                       PERM_VIEW_PROBLEM |
                       PERM_SUBMIT_PROBLEM |
                       PERM_VIEW_PROBLEM_SOLUTION |
                       PERM_CREATE_PROBLEM_SOLUTION |
                       PERM_VOTE_PROBLEM_SOLUTION |
                       PERM_REPLY_PROBLEM_SOLUTION |
                       PERM_VIEW_DISCUSSION |
                       PERM_CREATE_DISCUSSION |
                       PERM_REPLY_DISCUSSION |
                       PERM_VIEW_CONTEST |
                       PERM_VIEW_CONTEST_STATUS |
                       PERM_VIEW_TRAINING |
                       PERM_ATTEND_CONTEST)
ADMIN_PERMISSIONS = PERM_ALL
DOMAIN_SYSTEM = {'_id': DOMAIN_ID_SYSTEM,
                 'owner_uid': 0,
                 'roles': {ROLE_DEFAULT: DEFAULT_PERMISSIONS,
                           ROLE_ADMIN: ADMIN_PERMISSIONS}}
DOMAINS = [DOMAIN_SYSTEM]

# Users.
UID_GUEST = 1
UNAME_GUEST = 'Guest'
USER_GUEST = {'_id': UID_GUEST,
              'uname': UNAME_GUEST,
              'uname_lower': UNAME_GUEST.strip().lower(),
              'mail': '',
              'mail_lower': '',
              'salt': '',
              'hash': 'vj4|',
              'gender': constant.model.USER_GENDER_OTHER,
              'regat': datetime.datetime.utcfromtimestamp(0),
              'regip': '',
              'priv': PRIV_REGISTER_USER,
              'loginat': datetime.datetime.utcnow(),
              'loginip': '',
              'gravatar': '',
              # in every domains:
              'rp': 0.0,
              'rank': 0,
              'level': 0,
              'num_submit': 0,
              'num_accept': 0}
USERS = [USER_GUEST]

# Timezones.
TIMEZONES = collections.OrderedDict([(tz, tz) for tz in pytz.common_timezones])

# Key represents level
# Value represents percent
# E.g. (10, 1) means that people whose rank is less than 1% will get Level 10
LEVELS = collections.OrderedDict([(10, 1),
                                  (9, 2),
                                  (8, 10),
                                  (7, 20),
                                  (6, 30),
                                  (5, 40),
                                  (4, 70),
                                  (3, 90),
                                  (2, 95),
                                  (1, 100)])

# Footer extra HTMLs.
FOOTER_EXTRA_HTMLS = ['© 2005 - 2016 <a href="https://vijos.org/">Vijos.org</a>', version.get(),
                      '<a href="http://www.miitbeian.gov.cn/" target="_blank" rel="nofollow">' +
                      '沪ICP备14040537号</a>']
