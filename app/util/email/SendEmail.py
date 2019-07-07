#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication
from .mail_config import EMAIL_PORT, EMAIL_SERVICE, EMAIL_USER, EMAIL_PWD
import base64
from email import encoders


class SendEmail(object):
    _attachments = []

    def __init__(self, to_list, file):
        self.Email_service = EMAIL_SERVICE
        self.Email_port = EMAIL_PORT
        self.username = EMAIL_USER
        self.password = EMAIL_PWD
        self.to_list = to_list
        self.file = file
        print(file)

    def b64(self, headstr):
        """对邮件header及附件的文件名进行两次base64编码，防止outlook中乱码。email库源码中先对邮件进行一次base64解码然后组装邮件，所以两次编码"""
        headstr = '=?utf-8?b?' + base64.b64encode(headstr.encode('UTF-8')).decode() + '?='
        headstr = '=?utf-8?b?' + base64.b64encode(headstr.encode('UTF-8')).decode() + '?='
        return headstr

    def add_attachment(self):
        '''
            添加附件
        '''
        att = MIMEBase('application', 'octet-stream')
        att.set_payload(self.file)
        att.add_header('Content-Disposition', 'attachment', filename=('gbk', '', "接口测试报告.html"))
        encoders.encode_base64(att)
        self._attachments.append(att)

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
        #att1 = MIMEApplication(self.file,'base64', 'utf-8')
        #att1.add_header('Content-Disposition', 'attachment', filename=('gbk', '', '接口测试报告.html'))
        self.add_attachment()
        message.attach(self._attachments[0])

        try:
            # service = smtplib.SMTP()
            # service.connect(self.Email_service, 465)  # 25 为 SMTP 端口号
            # service.starttls()
            service = smtplib.SMTP_SSL(self.Email_service, 465)
            service.login(self.username, self.password)
            service.sendmail(self.username, self.to_list, message.as_string())
            print('邮件发送成功')
            service.close()
        except Exception as e:
            print(e)
            print('报错，邮件发送失败')


if __name__ == '__main__':
    pass
