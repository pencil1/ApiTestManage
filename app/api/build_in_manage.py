import types

from flask import jsonify, request
from . import api
from ..util.global_variable import *
import importlib


@api.route('/func/find', methods=['POST'])
def get_func():
    print(11111111)
    data = request.json
    func_name = data.get('funcName')
    if not func_name:
        return jsonify({'msg': '请输入文件名', 'status': 0})
    if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名不存在', 'status': 0})
    with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'r', encoding='utf8') as f:
        d = f.read()
    return jsonify({'msg': '获取成功', 'func_data': d, 'status': 1})


@api.route('/func/getAddress', methods=['POST'])
def get_funcs():
    for root, dirs, files in os.walk(os.path.abspath('.') + r'/func_list'):
        if '__init__.py' in files:
            files.remove('__init__.py')
        files = [{'value': f} for f in files]
        break
    return jsonify({'data': files, 'status': 1})


@api.route('/func/save', methods=['POST'])
def save_func():
    data = request.json
    func_data = data.get('funcData')
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名不存在', 'status': 0})
    with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
        f.write(func_data)
    return jsonify({'msg': '保存成功', 'status': 1})


def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)


@api.route('/func/check', methods=['POST'])
def check_func():
    data = request.json
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名不存在', 'status': 0})
    try:
        importlib.reload(importlib.import_module('func_list.{}'.format(func_name.replace('.py', ''))))
        return jsonify({'msg': '语法正确', 'status': 1})
    except Exception as e:
        print(e)
        return jsonify({'msg': '语法错误，请自行检查', 'error': e, 'status': 0})


@api.route('/func/create', methods=['POST'])
def create_func():
    data = request.json
    func_name = data.get('funcName')
    if not func_name:
        return jsonify({'msg': '文件名不能为空', 'status': 0})
    if os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名已存在', 'status': 0})
    with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
        pass
    return jsonify({'msg': '创建成功', 'status': 1})


@api.route('/func/remove', methods=['POST'])
def remove_func():
    data = request.json
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名不存在', 'status': 0})
    else:
        os.remove('{}/{}'.format(FUNC_ADDRESS, func_name))

    return jsonify({'msg': '删除成功', 'status': 1})
