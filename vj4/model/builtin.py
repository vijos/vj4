import collections
import datetime

# Permissions.
PERM_NONE = 0
PERM_SET_PERM = 1
PERM_CREATE_PROBLEM = 2
PERM_EDIT_PROBLEM = 4
PERM_VIEW_PROBLEM = 8
PERM_SUBMIT_PROBLEM = 16
PERM_VIEW_PROBLEM_SOLUTION = 32
PERM_SUBMIT_PROBLEM_SOLUTION = 64
PERM_VOTE_PROBLEM_SOLUTION = 128
PERM_REPLY_PROBLEM_SOLUTION = 256
PERM_VIEW_DISCUSSION = 512
PERM_CREATE_DISCUSSION = 1024
PERM_REPLY_DISCUSSION = 2048
PERM_TAIL_REPLY_DISCUSSION = 4096
PERM_READ_PROBLEM_DATA = 8192
PERM_VIEW_CONTEST = 16384
PERM_VIEW_CONTEST_STATUS = 32768
PERM_CREATE_CONTEST = 65536
PERM_VIEW_TRAINING = 131072
PERM_ATTEND_CONTEST = 262144
PERM_ALL = -1

# Privileges.
PRIV_NONE = 0
PRIV_SET_PRIV = 1
PRIV_SET_PERM = 2
PRIV_USER_PROFILE = 4
PRIV_REGISTER_USER = 8
PRIV_READ_RECORD_CODE = 16
PRIV_READ_PROBLEM_DATA = 32
PRIV_WRITE_RECORD = 64
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
USER_GENDER_MALE = 0
USER_GENDER_FEMALE = 1
USER_GENDER_OTHER = 2

USER_GENDERS = [USER_GENDER_MALE, USER_GENDER_FEMALE, USER_GENDER_OTHER]

UID_GUEST = 1
UNAME_GUEST = 'Guest'
USER_GUEST = {'_id': UID_GUEST,
              'uname': UNAME_GUEST,
              'uname_lower': UNAME_GUEST.strip().lower(),
              'mail': '',
              'mail_lower': '',
              'salt': '',
              'hash': 'vj4|',
              'gender': USER_GENDER_OTHER,
              'regat': datetime.datetime.utcfromtimestamp(0),
              'regip': '',
              'roles': {},
              'priv': PRIV_REGISTER_USER,
              'loginat': datetime.datetime.utcnow(),
              'loginip': '',
              'gravatar': ''}
USERS = [USER_GUEST]

# Code langs.
LANGS = collections.OrderedDict([('c', 'C'),
                                 ('cc', 'C++'),
                                 ('pas', 'Pascal'),
                                 ('java', 'Java'),
                                 ('py', 'Python')])

# View langs.
VIEW_LANGS = collections.OrderedDict([('zh_CN', '简体中文'),
                                      ('en', 'English')])

# Footer extra HTMLs.
FOOTER_EXTRA_HTMLS = ['© 2005 - 2016 <a href="https://vijos.org/">Vijos.org</a>', '{$GIT_REVISION}',
                      '<a href="http://www.miitbeian.gov.cn/" target="_blank" rel="nofollow">' +
                      '沪ICP备14040537号</a>']
