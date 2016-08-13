import collections
import datetime

from vj4 import constant
from vj4.util import version

# Permissions.
PERM_NONE = 0
PERM_SET_PERM = 1 << 0
PERM_CREATE_PROBLEM = 1 << 1
PERM_EDIT_PROBLEM = 1 << 2
PERM_VIEW_PROBLEM = 1 << 3
PERM_SUBMIT_PROBLEM = 1 << 4
PERM_VIEW_PROBLEM_SOLUTION = 1 << 5
PERM_SUBMIT_PROBLEM_SOLUTION = 1 << 6
PERM_VOTE_PROBLEM_SOLUTION = 1 << 7
PERM_REPLY_PROBLEM_SOLUTION = 1 << 8
PERM_VIEW_DISCUSSION = 1 << 9
PERM_CREATE_DISCUSSION = 1 << 10
PERM_REPLY_DISCUSSION = 1 << 11
PERM_TAIL_REPLY_DISCUSSION = 1 << 12
PERM_READ_PROBLEM_DATA = 1 << 13
PERM_VIEW_CONTEST = 1 << 14
PERM_VIEW_CONTEST_STATUS = 1 << 15
PERM_CREATE_CONTEST = 1 << 16
PERM_ATTEND_CONTEST = 1 << 17
PERM_VIEW_TRAINING = 1 << 18
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
PRIV_ALL = -1

# Roles.
ROLE_DEFAULT = 'default'
ROLE_ADMIN = 'admin'

# Domains.
DOMAIN_ID_SYSTEM = 'system'
DEFAULT_PERMISSIONS = (PERM_VIEW_PROBLEM |
                       PERM_SUBMIT_PROBLEM |
                       PERM_VIEW_PROBLEM_SOLUTION |
                       PERM_SUBMIT_PROBLEM_SOLUTION |
                       PERM_VOTE_PROBLEM_SOLUTION |
                       PERM_REPLY_PROBLEM_SOLUTION |
                       PERM_VIEW_DISCUSSION |
                       PERM_CREATE_DISCUSSION |
                       PERM_REPLY_DISCUSSION |
                       PERM_TAIL_REPLY_DISCUSSION |
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
              'roles': {},
              'priv': PRIV_REGISTER_USER,
              'loginat': datetime.datetime.utcnow(),
              'loginip': '',
              'gravatar': ''}
USERS = [USER_GUEST]

# View langs.
VIEW_LANGS = collections.OrderedDict([('zh_CN', '简体中文'),
                                      ('en', 'English')])

# Footer extra HTMLs.
FOOTER_EXTRA_HTMLS = ['© 2005 - 2016 <a href="https://vijos.org/">Vijos.org</a>', version.get(),
                      '<a href="http://www.miitbeian.gov.cn/" target="_blank" rel="nofollow">' +
                      '沪ICP备14040537号</a>']
