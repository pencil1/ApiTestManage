# ApiTestManage
感觉项目不错的点个star，你的支持是作者源源不断的动力~谢谢！！如有疑问可联系qq：362508572   或q群：700387899 或issue

前端传送门：https://github.com/pencil1/ApiTestWeb

线上demo地址：http://47.107.147.188/#/login （账号：ceshi 密码：123456）

## Environment
python => 3



## 安装依赖包

    pip install -r requirements.txt



## 使用flask命令，必须先设置：

设置flask的app(windows和linux的环境变量命令不一样，项目根目录下执行)

    set FLASK_APP=manage.py(windows)

    export FLASK_APP=manage.py(linux)


然后创建管理员账号（账号：admin，密码：123456，项目根目录下执行）

    flask initdata


## 开发环境

    python manage.py


## 生产环境

    gunicorn -c gunicorn_config.py manage:app


### 生产环境下的一些配置
由于懒，直接把flaskapi.conf文件替换nginx下的nginx.conf



## 数据库的迁移(数据库迁移不是必要步骤)

初始化：

    (venv)  flask db init 这个命令会在项目下创建 migrations 文件夹，所有迁移脚本都存放其中。


创建第一个版本：

    (venv) $ flask db migrate


运行升级

    (venv) $ flask db upgrade

后缀更新：
更新表格的字段 (models.py)
再次运行一下

    flask db migrate -> 相当于commit 更新到/migrate目录
    flask db upgrade -> 数据库会更新