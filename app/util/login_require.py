from functools import wraps
from flask_login import current_user
from flask import jsonify, current_app


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.login_manager._login_disabled:
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return jsonify({'msg': '登录超时,请重新登录', 'status': 0})
        return func(*args, **kwargs)

    return decorated_view
