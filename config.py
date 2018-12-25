# encoding: utf-8
import os
import multiprocessing
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time
from logging.handlers import TimedRotatingFileHandler

basedir = os.path.abspath(os.path.dirname(__file__))


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
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    return handler


class ConfigTask(object):
    """
    定时任务配置
    """
    jobstores = {'default': SQLAlchemyJobStore(url="sqlite:///" + os.path.join(basedir, "data.sqlite"))}
    executors = {'default': ThreadPoolExecutor(10), 'processpool': ProcessPoolExecutor(3)}

    def __init__(self):
        self.scheduler = BackgroundScheduler(jobstores=self.jobstores, executors=self.executors)


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

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/test'     # 123456表示密码，test代表数据库名称
    SQLALCHEMY_TRACK_MODIFICATIONS = True


config = {

    'default': DevelopmentConfig,
    'production': ProductionConfig,
}
