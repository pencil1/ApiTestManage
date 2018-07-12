# encoding: utf-8
"""
@author: pencil
@file: manage_linux.py
@time: 2018/7/12 16:39
"""
import os
from app import create_app

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    app.run()
