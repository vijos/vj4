import smtplibaio
from email.mime import text
from vj4.util import argmethod
from vj4.util import options

options.define('smtp_host', default='', help='SMTP server')
options.define('smtp_port', default=465, help='SMTP server')
options.define('smtp_user', default='', help='SMTP username')
options.define('smtp_password', default='', help='SMTP password')
options.define('mail_from', default='', help='Mail from')

async def send_mail(to: str, subject: str, content: str):
  msg = text.MIMEText(content, _subtype='html', _charset='UTF-8')
  msg['Subject'] = subject
  msg['From'] = options.options.mail_from
  msg['To'] = to
  server = smtplibaio.SMTP_SSL()
  await server.connect(host=options.options.smtp_host, port=options.options.smtp_port)
  await server.ehlo()
  await server.login(options.options.smtp_user, options.options.smtp_password)
  await server.sendmail(options.options.mail_from, to, msg.as_string())
  await server.quit()

if __name__ == '__main__':
  argmethod.invoke_by_args()
