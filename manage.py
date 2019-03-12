# encoding: utf-8
"""
@author: pencil
@file: manage.py
@time: 2018/10/31 16:39
"""
import os
from app import create_app, db
from app.models import User, Role
from flask_migrate import Migrate
import click

# production default
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db, render_as_batch=True)
# migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, User=User)


@app.cli.command()
def initdata():
    click.echo('Initializing the roles and permissions and admin...')
    Role.init_role()
    User.init_user()  # 初始化
    click.echo('Done.')

# manager.add_command("shell", Shell(make_context=make_shell_context))
# manager.add_command('db', MigrateCommand)
# manager.add_command('runserver', Server(host='127.0.0.1', port='8080'))  # host设置为本地地址后，局域网内的其他机子都可以访问

# manager.add_command('runserver', WSGIServer(('192.168.13.253', '8080'), app))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    # manager.run(default_command='runserver')
    # manager.run(default_command='shell')
