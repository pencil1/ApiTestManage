# coding     : utf-8
# @Time      : 2021/5/5 上午12:59
from random import randint
from faker import Faker
from faker.providers import BaseProvider

# 语言环境
# fake = Faker(['zh_CN', 'en_US', 'ja_JP'])

class ExtendProvider(BaseProvider):

    def sex(self):
        tmp = ['M', 'F']
        return tmp[randint(0, len(tmp) - 1)]

    def pay_type(self):
        tmp = ["ALI", 'WX']
        return tmp[randint(0, len(tmp) - 1)]


class BBCProvider(BaseProvider):

    def bbc_birthday(self):
        # 1-3是初级，4-6是高级
        tmp = ['2014年09月01日', '2014年3月1日', '2011年9月21日',
               '2011年3月2日', '2010年3月2日', '2007年10月1日']
        return tmp[randint(0, len(tmp) - 1)]


fakerist = Faker(locale='zh_CN')
# fakerist.add_provider(ExtendProvider)
# fakerist.add_provider(BBCProvider)

