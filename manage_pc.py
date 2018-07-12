# encoding: utf-8
"""
@author: pencil
@file: manage_linux.py
@time: 2018/7/12 16:39
"""
import os
from app import create_app, db
from app.models import User, Permisson, ApiMsg
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand
from gevent.pywsgi import WSGIServer
from gevent import monkey

# gevent的猴子魔法
monkey.patch_all()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, ApiCase=ApiMsg, )


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='127.0.0.1', port='8080'))  # host设置为本地地址后，局域网内的其他机子都可以访问


# manager.add_command('runserver', WSGIServer(('192.168.13.253', '8080'), app))


if __name__ == '__main__':
    # app.run(host='127.0.0.1', port=8080, debug=False)
    manager.run(default_command='runserver')
    # manager.run(default_command='shell')
