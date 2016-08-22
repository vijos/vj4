import collections
import datetime
import pytz

from vj4 import constant
from vj4.util import version

# Permissions.
# Domain settings.
PERM_NONE = 0
PERM_VIEW = 1 << 0
PERM_EDIT_PERM = 1 << 1
PERM_MOD_BADGE = 1 << 2
PERM_EDIT_DESCRIPTION = 1 << 3
PERM_TRANSFER = -1

# Problem and Record.
PERM_CREATE_PROBLEM = 1 << 4
PERM_EDIT_PROBLEM = 1 << 5
PERM_EDIT_PROBLEM_SELF = 1 << 6
PERM_VIEW_PROBLEM = 1 << 7
PERM_SUBMIT_PROBLEM = 1 << 8
PERM_READ_PROBLEM_DATA = 1 << 9
PERM_READ_PROBLEM_DATA_SELF = 1 << 10
PERM_READ_RECORD_CODE = 1 << 11
PERM_REJUDGE_PROBLEM = 1 << 12
PERM_REJUDGE = 1 << 13

# Problem Solution.
PERM_VIEW_PROBLEM_SOLUTION = 1 << 14
PERM_CREATE_PROBLEM_SOLUTION = 1 << 15
PERM_VOTE_PROBLEM_SOLUTION = 1 << 16
PERM_EDIT_PROBLEM_SOLUTION = 1 << 17
PERM_EDIT_PROBLEM_SOLUTION_SELF = 1 << 18
PERM_DELETE_PROBLEM_SOLUTION = 1 << 19
PERM_DELETE_PROBLEM_SOLUTION_SELF = 1 << 20
PERM_REPLY_PROBLEM_SOLUTION = 1 << 21
PERM_EDIT_PROBLEM_SOLUTION_REPLY = 1 << 22
PERM_EDIT_PROBLEM_SOLUTION_REPLY_SELF = 1 << 23
PERM_DELETE_PROBLEM_SOLUTION_REPLY = 1 << 24
PERM_DELETE_PROBLEM_SOLUTION_REPLY_SELF = 1 << 25

# Discussion.
PERM_VIEW_DISCUSSION = 1 << 26
PERM_CREATE_DISCUSSION = 1 << 27
PERM_HIGHLIGHT_DISCUSSION = 1 << 28
PERM_EDIT_DISCUSSION = 1 << 29
PERM_EDIT_DISCUSSION_SELF = 1 << 30
PERM_DELETE_DISCUSSION = 1 << 31
PERM_DELETE_DISCUSSION_SELF = 1 << 32
PERM_REPLY_DISCUSSION = 1 << 33
PERM_EDIT_DISCUSSION_REPLY = 1 << 34
PERM_EDIT_DISCUSSION_REPLY_SELF = 1 << 35
PERM_EDIT_DISCUSSION_REPLY_SELF_DISCUSSION = 1 << 36
PERM_DELETE_DISCUSSION_REPLY = 1 << 37
PERM_DELETE_DISCUSSION_REPLY_SELF = 1 << 38
PERM_DELETE_DISCUSSION_REPLY_SELF_DISCUSSION = 1 << 39

# Contest.
PERM_VIEW_CONTEST = 1 << 40
PERM_VIEW_CONTEST_STATUS = 1 << 41
PERM_VIEW_CONTEST_HIDDEN_STATUS = 1 << 42
PERM_CREATE_CONTEST = 1 << 43
PERM_ATTEND_CONTEST = 1 << 44

# Training.
PERM_VIEW_TRAINING = 1 << 45

PERM_ALL = -1

# Privileges.
PRIV_NONE = 0
PRIV_SET_PRIV = 1 << 0
PRIV_SET_PERM = 1 << 1
PRIV_USER_PROFILE = 1 << 2
PRIV_REGISTER_USER = 1 << 3
PRIV_READ_PROBLEM_DATA = 1 << 5
PRIV_READ_PRETEST_DATA = 1 << 7
PRIV_READ_PRETEST_DATA_SELF = 1 << 8
PRIV_READ_RECORD_CODE = 1 << 9
PRIV_WRITE_RECORD = 1 << 10
PRIV_CREATE_DOMAIN = 1 << 11
PRIV_VIEW_ALL_DOMAIN = 1 << 12
PRIV_MANAGE_ALL_DOMAIN = 1 << 13
PRIV_REJUDGE = 1 << 14
PRIV_ALL = -1

DEFAULT_PRIV = PRIV_USER_PROFILE | PRIV_CREATE_DOMAIN

# Roles.
ROLE_GUEST = 'guest'
ROLE_DEFAULT = 'default'
ROLE_ADMIN = 'admin'

# Domains.
DOMAIN_ID_SYSTEM = 'system'
BASIC_PERMISSIONS = (PERM_VIEW |
                     PERM_VIEW_PROBLEM |
                     PERM_VIEW_PROBLEM_SOLUTION |
                     PERM_VIEW_DISCUSSION |
                     PERM_VIEW_CONTEST |
                     PERM_VIEW_CONTEST_STATUS)
DEFAULT_PERMISSIONS = (PERM_VIEW |
                       PERM_VIEW_PROBLEM |
                       PERM_EDIT_PROBLEM_SELF |
                       PERM_SUBMIT_PROBLEM |
                       PERM_READ_PROBLEM_DATA_SELF |
                       PERM_VIEW_PROBLEM_SOLUTION |
                       PERM_CREATE_PROBLEM_SOLUTION |
                       PERM_VOTE_PROBLEM_SOLUTION |
                       PERM_EDIT_PROBLEM_SOLUTION_SELF |
                       PERM_DELETE_PROBLEM_SOLUTION_SELF |
                       PERM_REPLY_PROBLEM_SOLUTION |
                       PERM_EDIT_PROBLEM_SOLUTION_REPLY_SELF |
                       PERM_DELETE_PROBLEM_SOLUTION_REPLY_SELF |
                       PERM_VIEW_DISCUSSION |
                       PERM_CREATE_DISCUSSION |
                       PERM_EDIT_DISCUSSION_SELF |
                       PERM_REPLY_DISCUSSION |
                       PERM_EDIT_DISCUSSION_REPLY_SELF |
                       # PERM_EDIT_DISCUSSION_REPLY_SELF_DISCUSSION |
                       PERM_DELETE_DISCUSSION_REPLY_SELF |
                       PERM_DELETE_DISCUSSION_REPLY_SELF_DISCUSSION |
                       PERM_VIEW_CONTEST |
                       PERM_VIEW_CONTEST_STATUS |
                       PERM_VIEW_TRAINING |
                       PERM_ATTEND_CONTEST)
ADMIN_PERMISSIONS = PERM_ALL
DOMAIN_SYSTEM = {'_id': DOMAIN_ID_SYSTEM,
                 'owner_uid': 0,
                 'roles': {ROLE_GUEST: BASIC_PERMISSIONS,
                           ROLE_DEFAULT: DEFAULT_PERMISSIONS,
                           ROLE_ADMIN: ADMIN_PERMISSIONS},
                 'gravatar': '',
                 'name': 'Vijos 4'}
DOMAINS = [DOMAIN_SYSTEM]

# Users.
UID_SYSTEM = 0
UNAME_SYSTEM = 'Vijos 4'
USER_SYSTEM = {'_id': UID_SYSTEM,
              'uname': UNAME_SYSTEM,
              'uname_lower': UNAME_SYSTEM.strip().lower(),
              'mail': '',
              'mail_lower': '',
              'salt': '',
              'hash': 'vj4|',
              'gender': constant.model.USER_GENDER_OTHER,
              'regat': datetime.datetime.utcfromtimestamp(0),
              'regip': '',
              'priv': PRIV_NONE,
              'loginat': datetime.datetime.utcnow(),
              'loginip': '',
              'gravatar': '',
              # in every domains:
              'rp': 0.0,
              'rank': 0,
              'role': ROLE_GUEST,
              'level': 0,
              'num_submit': 0,
              'num_accept': 0}
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
              'role': ROLE_GUEST,
              'level': 0,
              'num_submit': 0,
              'num_accept': 0}
USERS = [USER_SYSTEM, USER_GUEST]

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
