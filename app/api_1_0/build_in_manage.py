import types
from flask import jsonify, request, current_app
from . import api, login_required
from ..util.global_variable import *
import importlib
from ..util.utils import parse_function, extract_functions
import traceback


@api.route('/func/find', methods=['POST'])
@login_required
def get_func():
    """ 获取函数文件信息 """
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
@login_required
def get_funcs():
    """ 查找所以函数文件 """
    for root, dirs, files in os.walk(os.path.abspath('.') + r'/func_list'):
        if '__init__.py' in files:
            files.remove('__init__.py')
        files = [{'value': f} for f in files]
        break
    return jsonify({'data': files, 'status': 1})


@api.route('/func/save', methods=['POST'])
@login_required
def save_func():
    """ 保存函数文件 """
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
@login_required
def check_func():
    """ 函数调试 """
    data = request.json
    func_file_name = data.get('funcFileName')
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_file_name)):
        return jsonify({'msg': '文件名不存在', 'status': 0})
    try:
        import_path = 'func_list.{}'.format(func_file_name.replace('.py', ''))
        func_list = importlib.reload(importlib.import_module(import_path))
        module_functions_dict = {name: item for name, item in vars(func_list).items() if
                                 isinstance(item, types.FunctionType)}

        ext_func = extract_functions(func_name)
        if len(ext_func) == 0:
            return jsonify({'msg': '函数解析失败，注意格式问题', 'status': 0})
        func = parse_function(ext_func[0])

        return jsonify({'msg': '请查看', 'status': 1, 'result': module_functions_dict[func['func_name']](*func['args'])})

    except Exception as e:
        current_app.logger.info(str(e))
        error_data = '\n'.join('{}'.format(traceback.format_exc()).split('↵'))
        return jsonify({'msg': '语法错误，请自行检查', 'result': error_data, 'status': 0})


@api.route('/func/create', methods=['POST'])
@login_required
def create_func():
    """ 创建函数文件 """
    data = request.json
    func_name = data.get('funcName')
    if func_name.find('.py') == -1:
        return jsonify({'msg': '请创建正确格式的py文件', 'status': 0})
    if not func_name:
        return jsonify({'msg': '文件名不能为空', 'status': 0})
    if os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名已存在', 'status': 0})
    with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
        pass
    return jsonify({'msg': '创建成功', 'status': 1})


@api.route('/func/remove', methods=['POST'])
@login_required
def remove_func():
    """ 删除函数文件 """
    data = request.json
    func_name = data.get('funcName')
    if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
        return jsonify({'msg': '文件名不存在', 'status': 0})
    else:
        os.remove('{}/{}'.format(FUNC_ADDRESS, func_name))
    return jsonify({'msg': '删除成功', 'status': 1})
