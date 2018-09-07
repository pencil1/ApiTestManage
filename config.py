# encoding: utf-8
import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import time

basedir = os.path.abspath(os.path.dirname(__file__))


class ConfigTask(object):
    jobstores = {'default': SQLAlchemyJobStore(url="sqlite:///" + os.path.join(basedir, "data.sqlite"))}
    executors = {'default': ThreadPoolExecutor(10), 'processpool': ProcessPoolExecutor(3)}

    def __init__(self):
        self.scheduler = BackgroundScheduler(jobstores=self.jobstores, executors=self.executors)


def config_log():
    log_file_str = os.path.abspath('..') + r'/logs/' + 'logger-' + time.strftime('%Y-%m-%d',
                                                                                 time.localtime(
                                                                                     time.time())) + '.log'
    handler = logging.FileHandler(log_file_str, encoding='UTF-8')
    handler.setLevel(logging.INFO)
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
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

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {

    'default': DevelopmentConfig
}
