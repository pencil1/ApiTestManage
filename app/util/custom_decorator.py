from functools import wraps
from flask import jsonify, current_app, request
from flask_login import current_user
import requests
import yaml, os

with open(r'{}/app/pom.yaml'.format(os.path.abspath('.')), 'r', encoding='utf-8') as f:
    common_config = yaml.load(f.read(), Loader=yaml.FullLoader)


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return jsonify({'msg': '登录过期,请重新登录', 'status': 0})
        return func(*args, **kwargs)

    return decorated_view


def login_required1(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        # print()
        # print(request.headers.get('userId'))
        header = dict()
        header['Authorization'] = request.headers.get('token')
        header['platform'] = common_config['platform']
        result = requests.get(f'{common_config["sso_ip"]}/sso/customer/info', headers=header)
        if result.json().get('code') == 401:
            return jsonify({'msg': '登录过期,请重新登录', 'status': 0})
        return func(*args, **kwargs)

    return decorated_view


def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            # User.query.filter_by(id=current_app.id).first().role_id
            if not current_user.can(permission_name):
                return jsonify({'msg': '没有该权限', 'status': 0})
            return func(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(func):
    return permission_required('ADMINISTER')(func)
