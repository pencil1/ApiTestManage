import gevent.monkey
import multiprocessing

"""
gunicorn的配置文件
"""
# gevent的猴子魔法 变成非阻塞
gevent.monkey.patch_all()

bind = '172.17.0.16:8080'

# 启动的进程数
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
worker_class = 'gunicorn.workers.ggevent.GeventWorker'