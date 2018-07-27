# ApiTestManage
如有疑问可联系qq：362508572

## Environment
python => 3

## start
开发环境：运行manage_pc.py
生产环境：运行manage_linux.py

### 生产环境下的一些配置
由于懒，直接把flaskapi.conf文件替换nginx下的nginx.conf

运行下面命令即可启动

    gunicorn -c gun_config.py manage_linux:app

### 数据库的迁移

第一次使用：
初始化：(venv)  python manage_pc.py db init 这个命令会在项目下创建 migrations 文件夹，所有迁移脚本都存放其中。

创建第一个版本：(venv) $ python manage_pc.py db migrate

运行升级 (venv) $ python manage_pc.py db upgrade

后缀更新：
更新表格的字段 (models.py)
再次运行一下 db migrate -> 相当于commit 更新到/migrate目录
db upgrade -> 数据库会更新