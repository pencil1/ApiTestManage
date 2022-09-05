#!/usr/bin/python
# -*- coding: UTF-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.application import MIMEApplication
from email import encoders
# from .mail_config import EMAIL_PORT, EMAIL_SERVICE
import requests
import time
import hmac
from urllib.parse import quote_plus
import base64
import hashlib

EMAIL_SERVICE = 'smtp.exmail.qq.com'
EMAIL_PORT = 465


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
        # att1 = MIMEApplication(self.file)

        att1 = MIMEText(self.file, 'base64', 'utf-8')
        # att1["Content-Type"] = 'application/octet-stream'
        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
        # att1["Content-Disposition"] = 'attachment; filename="test.txt"'
        # message.attach(att1)

        att1.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', '接口测试报告.html'))
        message.attach(att1)

        # try:
        service = smtplib.SMTP_SSL(host=self.Email_service)
        service.connect(host=self.Email_service, port=self.Email_port)
        # service.connect(self.Email_service, 25)  # 25 为 SMTP 端口号
        # service.ehlo()
        # service.starttls()
        service.login(self.username, self.password)
        service.sendmail(self.username, self.to_list, message.as_string(unixfrom=True))
        print('邮件发送成功')
        service.close()
        # except Exception as e:
        #     print(e)
        #     print('报错，邮件发送失败')
        #


def send_ding_ding_msg(address, webhook, secret, msg, title):
    """发送盯盯消息，参考地址：https://open.dingtalk.com/document/group/custom-robot-access"""

    timestamp = int(round(time.time() * 1000))
    # secret = 'SEC8a6c5ff6a0726b9ec29c8f90a8498cab18e60c5bde48bc25906c61229dd56dde'
    # secret = 'SECebef0a98a6a6c80bc0e653bb23e8980567f10496b5bf69d47c4be92f5450f499'
    secret_enc = bytes(secret, encoding='utf8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = bytes(string_to_sign, encoding='utf8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = quote_plus(base64.b64encode(hmac_code))
    url = webhook + '&timestamp={}&sign={}'.format(timestamp, sign)
    headers = {'Content-Type': 'application/json'}
    data = dict()
    # pic = "> ![screenshot]({})\n".format(pic)
    # pic = ''

    # data['msgtype'] = 'markdown'
    data = {
        "msgtype": "link",
        "link": {
            "text": f"{msg}",
            "title": f"{title}",
            "picUrl": "",
            "messageUrl": f"{address}"
        }
    }

    # data['at'] = {"atMobiles": list(phone),
    #               "isAtAll": False
    #               }
    # print(msg)
    r = requests.post(url, json=data, headers=headers, verify=False)
    # r = requests.post(url, json=data, headers=headers)
    print(r.text)
    # if r.json().get('errmsg') == "markdown is too long":
    #     print(r.text)


if __name__ == '__main__':
    # a = SendEmail('xiaofeifei0010@163.com', 'SGZDULWAYVWCAJNV', [ 'xiaofeifei0010@163.com', '15813316716@163.com'], """dfsdfs.""")
    # a = SendEmail('yuanzhenwei@aulton.com', 'kPB7hmVVU9FZgGCn', ['zhoulifang@aulton.com', ], """dfsdfs.""")
    # a.send_email()
    send_ding_ding_msg('http://127.0.0.1:8020/#/reportShow?')
