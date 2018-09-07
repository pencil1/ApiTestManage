# encoding: utf-8
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_moment import Moment
from flask_login import LoginManager
from config import config
from config import config_log
from config import ConfigTask
from .util import global_variable  # 初始化文件地址

login_manager = LoginManager()
login_manager.session_protection = 'None'
# login_manager.login_view = '.login'

db = SQLAlchemy()
moment = Moment()
scheduler = ConfigTask().scheduler
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.logger.addHandler(config_log())     # 初始化日志
    config[config_name].init_app(app)
    moment.init_app(app)

    # https://blog.csdn.net/yannanxiu/article/details/53426359 关于定时任务访问数据库时报错
    # 坑在这2个的区别 db = SQLAlchemy() db = SQLAlchemy(app)
    db.init_app(app)
    db.app = app
    db.create_all()

    login_manager.init_app(app)
    scheduler.start()     # 定时任务启动

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
