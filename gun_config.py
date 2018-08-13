import gevent.monkey
import multiprocessing

"""
gunicorn的配置文件
"""

gevent.monkey.patch_all()

debug = True
loglevel = 'info'
bind = '192.168.6.19:8080'

# 启动的进程数
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gunicorn.workers.ggevent.GeventWorker'

x_forwarded_for_header = 'X-FORWARDED-FOR'
