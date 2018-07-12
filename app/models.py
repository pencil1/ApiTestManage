# encoding: utf-8
from werkzeug.security import check_password_hash, generate_password_hash
from . import db, login_manager
import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app


class Permisson:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTRATOR = 0xff


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(64))
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})


class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True, unique=True)
    host = db.Column(db.String(), nullable=True)
    host_two = db.Column(db.String)
    host_three = db.Column(db.String)
    host_four = db.Column(db.String)
    principal = db.Column(db.String(), nullable=True)
    variables = db.Column(db.String())
    headers = db.Column(db.String())
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    modules = db.relationship('Module', backref='project', lazy='dynamic')
    scenes = db.relationship('Scene', backref='project', lazy='dynamic')


class Scene(db.Model):
    __tablename__ = 'scene'
    id = db.Column(db.Integer(), primary_key=True)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    desc = db.Column(db.String())
    func_address = db.Column(db.String())
    variables = db.Column(db.String())
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class SceneConfig(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer(), primary_key=True)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String())
    variables = db.Column(db.String())
    func_address = db.Column(db.String())
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class Module(db.Model):
    __tablename__ = 'module'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    num = db.Column(db.Integer(), nullable=True)
    created_time = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    api_msg = db.relationship('ApiMsg', backref='module', lazy='dynamic')


class ApiMsg(db.Model):
    __tablename__ = 'apiMsg'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    num = db.Column(db.Integer(), nullable=True)
    name = db.Column(db.String(), nullable=True)
    desc = db.Column(db.String(), nullable=True)
    variable_type = db.Column(db.String(), nullable=True)
    status_url = db.Column(db.String(), nullable=True)
    func_address = db.Column(db.String())
    up_func = db.Column(db.String())
    down_func = db.Column(db.String())
    method = db.Column(db.String(), nullable=True)
    variables = db.Column(db.String())
    url = db.Column(db.String(), nullable=True)
    extract = db.Column(db.String())
    validate = db.Column(db.String())
    headers = db.Column(db.String())
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'))  # module指的是 __tablename__


class ApiCase(db.Model):
    __tablename__ = 'apiCase'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    num = db.Column(db.Integer(), nullable=True)
    status = db.Column(db.String())
    name = db.Column(db.String())
    up_func = db.Column(db.String())
    down_func = db.Column(db.String())

    variables = db.Column(db.String())
    status_variables = db.Column(db.String)
    extract = db.Column(db.String())
    status_extract = db.Column(db.String)
    validate = db.Column(db.String())
    status_validate = db.Column(db.String)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'))
    apiMsg_id = db.Column(db.Integer, db.ForeignKey('apiMsg.id'))


class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    name = db.Column(db.String(), nullable=True)
    belong_pro = db.Column(db.String(), nullable=True)
    read_status = db.Column(db.String, nullable=True)
    data = db.Column(db.String(65500), nullable=True)


class Task(db.Model):  # 定时任务的
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer())
    task_name = db.Column(db.String(52))  # 任务名称
    task_config_time = db.Column(db.String(252), nullable=True)  # 任务执行时间
    timestamp = db.Column(db.DateTime(), default=datetime.datetime.now())  # 任务的创建时间
    project_name = db.Column(db.String(), nullable=True)
    scene_names = db.Column(db.String())
    task_type = db.Column(db.String(), nullable=True)
    task_to_email_address = db.Column(db.String(252))  # 收件人邮箱
    task_send_email_address = db.Column(db.String(252))  # 维护本计划的人的邮箱
    status = db.Column(db.String(), default=u'创建')  # 任务的运行状态，默认是创建


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
