# encoding: utf-8
from werkzeug.security import check_password_hash, generate_password_hash
from . import db, login_manager
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from collections import OrderedDict

roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')))


class BaseModel(db.Model):
    """ 基类模型 """
    __abstract__ = True

    # is_delete = db.Column(db.SmallInteger, default=0, comment='通过更改状态来判断记录是否被删除, 0数据有效, 1数据已删除')
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now, comment='修改时间')

    def save(self, attrs_dict):
        """ 插入数据 """
        for key, value in attrs_dict.items():
            if hasattr(self, key) and key != 'id':
                setattr(self, key, value)

    # def delete(self):
    #     """ 软删除 """
    #     self.is_delete = 1

    @classmethod
    def get_first(cls, **kwargs):
        """ 获取第一条数据 """
        return cls.query.filter_by(**kwargs).first()

    @classmethod
    def get_all(cls, **kwargs):
        """ 获取全部数据 """
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def get_filter_by(cls, **kwargs):
        """ 获取filter_by对象 """
        return cls.query.filter_by(**kwargs)

    @classmethod
    def get_filter(cls, **kwargs):
        """ 获取filter对象 """
        return cls.query.filter(**kwargs)

    @classmethod
    def get_new_num(cls, num, **kwargs):
        """
        自动返回 model表中**kwargs筛选条件下的已存在编号num的最大值+1，用于插入数据时排序
        如：用例集表中，某project_id对应的用例集编号
        num     数据名     project_id
        1       name        6
        2       name        2
        2       name        6
        返回3
        """
        if not num:
            if not cls.get_all(**kwargs):
                return 1
            else:
                return cls.get_filter_by(**kwargs).order_by(cls.num.desc()).first().num + 1
        return num

    def to_dict(self):
        """ 自定义序列化器，把模型的每个字段转为字典，方便返回给前端 """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in [
            'created_time', 'update_time']}


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True, comment='主键，自增')
    name = db.Column(db.String(30), unique=True, comment='角色名称')
    users = db.relationship('User', back_populates='role')
    permission = db.relationship('Permission', secondary=roles_permissions, back_populates='role')

    @staticmethod
    def init_role():
        roles_permissions_map = OrderedDict()
        roles_permissions_map[u'测试人员'] = ['COMMON']
        roles_permissions_map[u'管理员'] = ['COMMON', 'ADMINISTER']
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
                role.permission = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permission.append(permission)
                db.session.commit()
        print('Role and permission created successfully')


class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True, comment='主键，自增')
    name = db.Column(db.String(30), unique=True, comment='权限名称')
    role = db.relationship('Role', secondary=roles_permissions, back_populates='permission')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, comment='主键，自增')
    account = db.Column(db.String(64), unique=True, index=True, comment='账号')
    password_hash = db.Column(db.String(128), comment='密码')
    name = db.Column(db.String(64), comment='姓名')
    status = db.Column(db.Integer, comment='状态，1为启用，2为冻结')
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), comment='所属的角色id')
    role = db.relationship('Role', back_populates='users')
    created_time = db.Column(db.DateTime, index=True, default=datetime.now)
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)

    @staticmethod
    def init_user():
        user = User.query.filter_by(name='管理员').first()
        if user:
            print('The administrator account already exists')
            print('--' * 30)
            return
        else:
            user = User(name=u'管理员', account='admin', password='123456', status=1, role_id=2)
            db.session.add(user)
            db.session.commit()
            print('Administrator account created successfully')
            print('--' * 30)

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

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permission


class Project(BaseModel):
    __tablename__ = 'project'
    user_id = db.Column(db.Integer(), nullable=True, comment='所属的用户id')
    name = db.Column(db.String(64), nullable=True, unique=True, comment='项目名称')
    host = db.Column(db.String(1024), nullable=True, comment='测试环境')
    host_two = db.Column(db.String(1024), comment='开发环境')
    host_three = db.Column(db.String(1024), comment='线上环境')
    host_four = db.Column(db.String(1024), comment='备用环境')
    environment_choice = db.Column(db.String(16), comment='环境选择，first为测试，以此类推')
    principal = db.Column(db.String(16), nullable=True)
    variables = db.Column(db.String(2048), comment='项目的公共变量')
    headers = db.Column(db.String(1024), comment='项目的公共头部信息')
    func_file = db.Column(db.String(128), comment='函数地址')
    modules = db.relationship('Module', order_by='Module.num.asc()', lazy='dynamic')
    configs = db.relationship('Config', order_by='Config.num.asc()', lazy='dynamic')
    case_sets = db.relationship('CaseSet', order_by='CaseSet.num.asc()', lazy='dynamic')


class Module(db.Model):
    __tablename__ = 'module'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    name = db.Column(db.String(64), nullable=True, comment='接口模块')
    num = db.Column(db.Integer(), nullable=True, comment='模块序号')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')
    api_msg = db.relationship('ApiMsg', order_by='ApiMsg.num.asc()', lazy='dynamic')
    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    num = db.Column(db.Integer(), nullable=True, comment='配置序号')
    name = db.Column(db.String(128), comment='配置名称')
    variables = db.Column(db.Text(), comment='配置参数')
    func_address = db.Column(db.String(128), comment='配置函数')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')
    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class CaseSet(db.Model):
    __tablename__ = 'case_set'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    num = db.Column(db.Integer(), nullable=True, comment='用例集合序号')
    name = db.Column(db.String(256), nullable=True, comment='用例集名称')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')
    cases = db.relationship('Case', order_by='Case.num.asc()', lazy='dynamic')
    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class Case(BaseModel):
    __tablename__ = 'case'
    num = db.Column(db.Integer(), nullable=True, comment='用例序号')
    name = db.Column(db.String(128), nullable=True, comment='用例名称')
    desc = db.Column(db.String(256), comment='用例描述')
    func_address = db.Column(db.String(256), comment='用例需要引用的函数')
    variable = db.Column(db.Text(), comment='用例公共参数')
    times = db.Column(db.Integer(), nullable=True, comment='执行次数')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), comment='所属的项目id')
    case_set_id = db.Column(db.Integer, db.ForeignKey('case_set.id'), comment='所属的用例集id')
    environment = db.Column(db.Integer(), comment='环境类型')


class ApiMsg(db.Model):
    __tablename__ = 'api_msg'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    num = db.Column(db.Integer(), nullable=True, comment='接口序号')
    name = db.Column(db.String(128), nullable=True, comment='接口名称')
    desc = db.Column(db.String(256), nullable=True, comment='接口描述')
    variable_type = db.Column(db.String(32), nullable=True, comment='参数类型选择')
    status_url = db.Column(db.String(32), nullable=True, comment='基础url,序号对应项目的环境')
    up_func = db.Column(db.String(128), comment='接口执行前的函数')
    down_func = db.Column(db.String(128), comment='接口执行后的函数')
    method = db.Column(db.String(32), nullable=True, comment='请求方式')
    variable = db.Column(db.Text(), comment='form-data形式的参数')
    json_variable = db.Column(db.Text(), comment='json形式的参数')
    param = db.Column(db.Text(), comment='url上面所带的参数')
    url = db.Column(db.String(256), nullable=True, comment='接口地址')
    skip = db.Column(db.String(256), comment='跳过判断')
    extract = db.Column(db.String(2048), comment='提取信息')
    validate = db.Column(db.String(2048), comment='断言信息')
    header = db.Column(db.String(2048), comment='头部信息')
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), comment='所属的接口模块id')
    project_id = db.Column(db.Integer, nullable=True, comment='所属的项目id')
    created_time = db.Column(db.DateTime, index=True, default=datetime.now)
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class CaseData(db.Model):
    __tablename__ = 'case_data'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    num = db.Column(db.Integer(), nullable=True, comment='步骤序号，执行顺序按序号来')
    status = db.Column(db.String(16), comment='状态，true表示执行，false表示不执行')
    name = db.Column(db.String(128), comment='步骤名称')
    up_func = db.Column(db.String(256), comment='步骤执行前的函数')
    down_func = db.Column(db.String(256), comment='步骤执行后的函数')
    skip = db.Column(db.String(64), comment='跳过判断函数')
    time = db.Column(db.Integer(), default=1, comment='执行次数')
    param = db.Column(db.Text(), default=u'[]')
    status_param = db.Column(db.String(64), default=u'[true, true]')
    variable = db.Column(db.Text())
    json_variable = db.Column(db.Text())
    status_variables = db.Column(db.String(64))
    extract = db.Column(db.String(2048))
    status_extract = db.Column(db.String(64))
    validate = db.Column(db.String(2048))
    status_validate = db.Column(db.String(64))
    header = db.Column(db.String(2048))
    status_header = db.Column(db.String(64))
    case_id = db.Column(db.Integer, db.ForeignKey('case.id'))
    api_msg_id = db.Column(db.Integer, db.ForeignKey('api_msg.id'))
    created_time = db.Column(db.DateTime, index=True, default=datetime.now)
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class Report(db.Model):
    __tablename__ = 'report'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    case_names = db.Column(db.String(128), nullable=True, comment='用例的名称集合')
    read_status = db.Column(db.String(16), nullable=True, comment='阅读状态')
    performer = db.Column(db.String(16), nullable=True, comment='执行者')
    project_id = db.Column(db.String(16), nullable=True)
    result = db.Column(db.String(16), comment='结果')
    create_time = db.Column(db.DateTime(), index=True, default=datetime.now)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, comment='主键，自增')
    num = db.Column(db.Integer(), comment='任务序号')
    task_name = db.Column(db.String(64), comment='任务名称')
    task_config_time = db.Column(db.String(256), nullable=True, comment='cron表达式')
    set_id = db.Column(db.String(2048))
    case_id = db.Column(db.String(2048))
    task_type = db.Column(db.String(16))
    task_to_email_address = db.Column(db.String(256), comment='收件人邮箱')
    task_send_email_address = db.Column(db.String(256), comment='发件人邮箱')
    email_password = db.Column(db.String(256), comment='发件人邮箱密码')
    status = db.Column(db.String(16), default=u'创建', comment='任务的运行状态，默认是创建')
    project_id = db.Column(db.String(16), nullable=True)
    send_email_status = db.Column(db.String(16))
    created_time = db.Column(db.DateTime(), default=datetime.now, comment='任务的创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class TestCaseFile(db.Model):
    __tablename__ = 'test_case_file'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    num = db.Column(db.Integer(), nullable=True, comment='测试用例文件序号')
    name = db.Column(db.String(128), nullable=True, comment='测试用例文件名称')

    status = db.Column(db.Integer(), comment='0代表文件夹；1代表用例文件')
    higher_id = db.Column(db.Integer(), comment='上级id，父级为0')
    user_id = db.Column(db.Integer(), comment='创建人id')

    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class FuncFile(db.Model):
    __tablename__ = 'func_file'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    name = db.Column(db.String(128), nullable=True, comment='内置函数文件名称')
    num = db.Column(db.Integer(), nullable=True, comment='内置函数文件序号')
    status = db.Column(db.Integer(), comment='0代表文件夹；1代表用例文件')
    higher_id = db.Column(db.Integer(), comment='上级id，父级为0')
    user_id = db.Column(db.Integer(), comment='创建人id')

    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


class Logs(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer(), primary_key=True, comment='主键，自增')
    ip = db.Column(db.String(128), comment='ip')
    uid = db.Column(db.String(128), comment='uid')
    url = db.Column(db.String(128), comment='url')

    created_time = db.Column(db.DateTime, index=True, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, index=True, default=datetime.now, onupdate=datetime.now)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
