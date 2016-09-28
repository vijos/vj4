import aiosmtplib as asmtp
from email.mime import text

from vj4.util import argmethod
from vj4.util import options

options.define('smtp_host', default='', help='SMTP server')
options.define('smtp_port', default=465, help='SMTP server')
options.define('smtp_user', default='', help='SMTP username')
options.define('smtp_password', default='', help='SMTP password')
options.define('mail_from', default='', help='Mail from')


@argmethod.wrap
async def send_mail(to: str, subject: str, content: str):
  msg = text.MIMEText(content, _subtype='html', _charset='UTF-8')
  msg['Subject'] = subject
  msg['From'] = options.mail_from
  msg['To'] = to

  async with asmtp.SMTP_SSL(hostname=options.smtp_host, port=options.smtp_port) as server:
    await server.ehlo()
    await server.login(options.smtp_user, options.smtp_password)
    await server.sendmail(options.mail_from, to, msg.as_string())

if __name__ == '__main__':
  argmethod.invoke_by_args()
