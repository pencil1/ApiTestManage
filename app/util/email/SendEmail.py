#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication
from .mail_config import EMAIL_PORT, EMAIL_SERVICE


class SendEmail(object):
    def __init__(self, username, password, to_list, file):
        self.Email_service = EMAIL_SERVICE
        self.Email_port = EMAIL_PORT
        self.username = username
        self.password = password
        self.to_list = to_list
        self.file = file

    def send_email(self):
        # 第三方 SMTP 服务

        message = MIMEMultipart()
        part = MIMEText('Dear all:\n       附件为接口自动化测试报告，此为自动发送邮件，请勿回复，谢谢！', 'plain', 'utf-8')
        message.attach(part)
        message['From'] = Header("测试组", 'utf-8')
        message['To'] = Header(''.join(self.to_list), 'utf-8')
        subject = '接口测试邮件'
        message['Subject'] = Header(subject, 'utf-8')

        # 添加附件
        att1 = MIMEApplication(self.file)
        att1.add_header('Content-Disposition', 'attachment', filename=('gbk', '', '接口测试报告.html'))
        message.attach(att1)

        try:
            service = smtplib.SMTP()
            service.connect(self.Email_service, 25)  # 25 为 SMTP 端口号
            service.starttls()
            service.login(self.username, self.password)
            service.sendmail(self.username, self.to_list, message.as_string())
            print('邮件发送成功')
            service.close()
        except Exception as e:
            print(e)
            print('报错，邮件发送失败')


if __name__ == '__main__':
    pass
