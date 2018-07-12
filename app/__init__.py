# encoding: utf-8
"""
@author: lileilei
@site: 
@software: PyCharm
@file: __init__.py.py
@time: 2017/7/13 16:38
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from config import config
from apscheduler.schedulers.background import BackgroundScheduler
from config import jobstores, executors
import logging
import time

login_manager = LoginManager()
login_manager.session_protection = 'None'
# login_manager.login_view = '.login'

bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()

basedir = os.path.abspath(os.path.dirname(__file__))
scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)


def config_log():
    log_file_str = os.path.abspath('..') + r'/logs/' + 'logger-' + time.strftime('%Y-%m-%d',
                                                                                 time.localtime(time.time())) + '.log'
    handler = logging.FileHandler(log_file_str, encoding='UTF-8')
    handler.setLevel(logging.INFO)
    logging_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    return handler


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.logger.addHandler(config_log())
    # app.logger.addFilter(handler)
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    # scheduler.init_app(app)
    moment.init_app(app)

    # https://blog.csdn.net/yannanxiu/article/details/53426359 关于定时任务访问数据库时报错
    # 坑在这2个的区别 db = SQLAlchemy() db = SQLAlchemy(app)
    db.init_app(app)
    db.app = app
    db.create_all()

    login_manager.init_app(app)
    scheduler.start()

    # from .main import main as main_blueprint
    # app.register_blueprint(main_blueprint)

    # from .pro import pro as pro_blueprint
    # app.register_blueprint(pro_blueprint, url_prefix='/pro')
    #
    # from .DataTool import DataTools as DataTool_blueprint
    # app.register_blueprint(DataTool_blueprint, url_prefix='/dataTool')
    #
    # from .TestCase import TestCases as TestCase_blueprint
    # app.register_blueprint(TestCase_blueprint, url_prefix='/TestCase')
    #
    # from .testpage import testpages as testpage_blueprint
    # app.register_blueprint(testpage_blueprint, url_prefix='/testpage')
    #
    # from .apiManage import apiManages as apiManages_blueprint
    # app.register_blueprint(apiManages_blueprint, url_prefix='/apiManage')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # from .api.model import api as api_blueprint
    # app.register_blueprint(api_blueprint, url_prefix='/api')
    return app
