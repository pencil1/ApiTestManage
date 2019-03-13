# encoding: utf-8
import os
import multiprocessing
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging
import time
from logging.handlers import TimedRotatingFileHandler
import urllib3.fields as f
import six
import email

basedir = os.path.abspath(os.path.dirname(__file__))


def my_format_header_param(name, value):
    if not any(ch in value for ch in '"\\\r\n'):
        result = '%s="%s"' % (name, value)
        try:
            result.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        else:
            return result
    if not six.PY3 and isinstance(value, six.text_type):  # Python 2:
        value = value.encode('utf-8')
    value = email.utils.encode_rfc2231(value, 'utf-8')
    value = '%s*=%s' % (name, value)
    return value


# 猴子补丁，修复request上传文件时，不能传中文
f.format_header_param = my_format_header_param


class SafeLog(TimedRotatingFileHandler):
    """
    因为TimedRotatingFileHandler在多进程访问log文件时，切分log日志会报错文件被占用，所以修复这个问题
    """

    def __init__(self, *args, **kwargs):
        super(SafeLog, self).__init__(*args, **kwargs)
        self.suffix_time = ""
        self.origin_basename = self.baseFilename

    def shouldRollover(self, record):
        time_tuple = time.localtime()
        if self.suffix_time != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                self.origin_basename + '.' + self.suffix_time):
            return 1
        else:
            return 0

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = self.origin_basename + '.' + self.suffix_time

        self.mode = 'a'

        with multiprocessing.Lock():
            if self.backupCount > 0:
                for s in self.getFilesToDelete():
                    os.remove(s)

        if not self.delay:
            self.stream = self._open()

    def getFilesToDelete(self):
        # 将源代码的 self.baseFilename 改为 self.origin_basename
        dir_name, base_name = os.path.split(self.origin_basename)
        file_names = os.listdir(dir_name)
        result = []
        prefix = base_name + "."
        p_len = len(prefix)
        for fileName in file_names:
            if fileName[:p_len] == prefix:
                suffix = fileName[p_len:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dir_name, fileName))
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result


def config_log():
    """
    日志配置
    :return:
    """
    handler = SafeLog(filename=os.path.abspath('..') + r'/logs/' + 'logger', interval=1, backupCount=50, when="D",
                      encoding='UTF-8')
    handler.setLevel(logging.INFO)
    handler.suffix = "%Y-%m-%d.log"
    logging_format = logging.Formatter('%(asctime)s - %(levelname)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    # handler.setFormatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    return handler


class Config:
    SECRET_KEY = 'BaSeQuie'
    basedir = os.path.abspath(os.path.dirname(__file__))

    # sqlite数据库的地址
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "data.sqlite")
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CSRF_ENABLED = True
    UPLOAD_FOLDER = '/upload'
    DEBUG = True
    SCHEDULER_API_ENABLED = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    SCHEDULER_JOBSTORES = {'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)}


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@192.168.6.19:3306/api_test'  # 123456表示密码，test代表数据库名称
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@47.107.147.188:3306/api_test'  # 123456表示密码，test代表数据库名称
    SCHEDULER_JOBSTORES = {'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)}
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_POOL_TIMEOUT = 20


config = {

    'default': DevelopmentConfig,
    'production': ProductionConfig,
}
