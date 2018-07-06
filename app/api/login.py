from flask import jsonify, request
from . import api
from app.models import *
import json
from flask_login import login_user, logout_user, login_required


@api.route('/register', methods=['GET', 'POST'])
def register():
    data = request.json
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(name=name).first():
        return jsonify({'msg': '名字已存在', 'status': 0})
    elif User.query.filter_by(username=username).first():
        return jsonify({'msg': '账号已存在', 'status': 0})
    user = User(name=name, username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'msg': '注册成功', 'status': 1})


@api.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'msg': '登出成功', 'status': 1})


@api.route('/login', methods=['GET', 'POST'])
def login():
    if request.json:
        data = request.json
    elif request.form:
        data = request.form
    else:
        data = request.data
        data = bytes.decode(data)
        data = json.loads(data)
        print(data)
    # data = request.json
    # username1 = request.form
    # print(username1.get('password'))
    # # username1 = bytes.decode(username1)
    # print(222)
    # username = username1.get('username')
    # password = username1.get('password')
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user is None:
        return jsonify({'msg': '账号错误或不存在', 'status': 0})
    elif not user.verify_password(password):
        return jsonify({'msg': '密码错误', 'status': 0})
    else:
        login_user(user, True)
        token = user.generate_reset_token()
        token = bytes.decode(token)
        return jsonify({'msg': '登录成功', 'status': 1, 'token': token, 'name': user.name})


@api.route('/proGather/list1', methods=['GET', 'POST'])
@login_required
def get_pro_gather1():
    _pros = Project.query.all()
    pro = {}
    for p in _pros:
        _gats = Module.query.filter_by(project_id=p.id).all()
        if _gats:
            pro[p.pro_name] = [_gat.gather_name for _gat in _gats]
        else:
            pro[p.pro_name] = ['']
    return jsonify(pro)
