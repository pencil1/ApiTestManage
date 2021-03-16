from flask import jsonify, request, current_app
from . import api, login_required
from ..util.global_variable import *
import traceback
from ..util.utils import *
from app.models import FuncFile, db
from flask_login import current_user


@api.route('/FuncFile/add', methods=['POST'])
@login_required
def add_func_file():
    """ 添加函数文件 """
    data = request.json
    name = data.get('name')
    higher_id = data.get('higherId')
    status = data.get('status')
    ids = data.get('id')
    if not name:
        return jsonify({'msg': '名称不能为空', 'status': 0})
    num = auto_num(data.get('num'), FuncFile)
    if ids:
        old_data = FuncFile.query.filter_by(id=ids).first()
        if status == 1:
            os.rename('{}/{}'.format(FUNC_ADDRESS, old_data.name), '{}/{}'.format(FUNC_ADDRESS, name))
        old_data.name = name
        old_data.num = num
        old_data.higher_id = higher_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if os.path.exists('{}/{}'.format(FUNC_ADDRESS, name)):
            return jsonify({'msg': '文件名已存在', 'status': 0})
        _new = FuncFile(name=name, higher_id=higher_id, num=num, status=status, user_id=current_user.id)
        db.session.add(_new)
        db.session.commit()
        if status == 1:
            with open('{}/{}'.format(FUNC_ADDRESS, name ), 'w', encoding='utf8') as f:
                pass

        return jsonify({'msg': '新建成功', 'status': 1, 'id': _new.id, 'higher_id': _new.higher_id, })


#
@api.route('/FuncFile/find', methods=['POST'])
@login_required
def find_func_file():
    """ 查找函数文件 """
    data = request.json
    privates = data.get('privates')

    kwargs = {'higher_id': 0}
    if privates:
        kwargs['user_id'] = current_user.id

    def get_data(all_data):
        if isinstance(all_data, list):
            if all_data:
                _t = []
                for d in all_data:
                    _t.append(get_data(d))
                return _t
            else:
                return []
        else:
            _d = {'id': all_data.id, 'num': all_data.num, 'name': all_data.name, 'status': all_data.status,
                  'higher_id': all_data.higher_id}
            if all_data.status == 0:
                kwargs['higher_id'] = all_data.id
                _d['children'] = get_data(
                    FuncFile.query.filter_by(**kwargs).order_by(FuncFile.num.asc()).all())
            return _d

    end_data = get_data(FuncFile.query.filter_by(**kwargs).order_by(FuncFile.num.asc()).all())

    return jsonify({'status': 1, 'data': end_data, 'msg': 1})


@api.route('/FuncFile/get', methods=['POST'])
@login_required
def get_func_file():
    """ 返回函数文件内容 """
    data = request.json
    ids = data.get('id')
    func_name = FuncFile.query.filter_by(id=ids).first().name
    with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'r', encoding='utf8') as f:
        d = f.read()
    print(d)
    print('{}/{}'.format(FUNC_ADDRESS, func_name))
    return jsonify({'msg': '获取成功', 'func_data': d, 'status': 1})


@api.route('/FuncFile/save', methods=['POST'])
@login_required
def save_func_file():
    """ 返回待编辑用例集合 """
    data = request.json
    func_data = data.get('data')
    ids = data.get('ids')
    func_name = FuncFile.query.filter_by(id=ids).first().name
    with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
        f.write(func_data)

    return jsonify({'msg': '保存成功', 'status': 1})


#
@api.route('/FuncFile/del', methods=['POST'])
@login_required
def del_func_file():
    """ 删除函数文件 """
    data = request.json
    ids = data.get('id')
    _edit = FuncFile.query.filter_by(id=ids).first()
    case = FuncFile.query.filter_by(higher_id=ids).first()
    if current_user.id != _edit.user_id:
        return jsonify({'msg': '不能删除别人创建的', 'status': 0})
    if case:
        return jsonify({'msg': '请先删除该文件的下级内容', 'status': 0})
    if _edit.status == 1:
        os.remove('{}/{}'.format(FUNC_ADDRESS, _edit.name))
    db.session.delete(_edit)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


# ------------------------------------------------
#
# @api.route('/func/find', methods=['POST'])
# @login_required
# def get_func():
#     """ 获取函数文件信息 """
#     data = request.json
#     func_name = data.get('funcName')
#     if not func_name:
#         return jsonify({'msg': '请输入文件名', 'status': 0})
#     if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
#         return jsonify({'msg': '文件名不存在', 'status': 0})
#     with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'r', encoding='utf8') as f:
#         d = f.read()
#     return jsonify({'msg': '获取成功', 'func_data': d, 'status': 1})
#
#
# @api.route('/func/getAddress', methods=['POST'])
# @login_required
# def get_funcs():
#     """ 查找所以函数文件 """
#     for root, dirs, files in os.walk(os.path.abspath('.') + r'/func_list'):
#         if '__init__.py' in files:
#             files.remove('__init__.py')
#         files = [{'value': f} for f in files]
#         break
#     return jsonify({'data': files, 'status': 1})
#
#
# @api.route('/func/save', methods=['POST'])
# @login_required
# def save_func():
#     """ 保存函数文件 """
#     data = request.json
#     func_data = data.get('funcData')
#     func_name = data.get('funcName')
#     if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
#         return jsonify({'msg': '文件名不存在', 'status': 0})
#     with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
#         f.write(func_data)
#     return jsonify({'msg': '保存成功', 'status': 1})
#
#
# def is_function(tup):
#     """ Takes (name, object) tuple, returns True if it is a function.
#     """
#     name, item = tup
#     return isinstance(item, types.FunctionType)
#
#
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
#
#
# @api.route('/func/create', methods=['POST'])
# @login_required
# def create_func():
#     """ 创建函数文件 """
#     data = request.json
#     func_name = data.get('funcName')
#     if func_name.find('.py') == -1:
#         return jsonify({'msg': '请创建正确格式的py文件', 'status': 0})
#     if not func_name:
#         return jsonify({'msg': '文件名不能为空', 'status': 0})
#     if os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
#         return jsonify({'msg': '文件名已存在', 'status': 0})
#     with open('{}/{}'.format(FUNC_ADDRESS, func_name), 'w', encoding='utf8') as f:
#         pass
#     return jsonify({'msg': '创建成功', 'status': 1})
#
#
# @api.route('/func/remove', methods=['POST'])
# @login_required
# def remove_func():
#     """ 删除函数文件 """
#     data = request.json
#     func_name = data.get('funcName')
#     if not os.path.exists('{}/{}'.format(FUNC_ADDRESS, func_name)):
#         return jsonify({'msg': '文件名不存在', 'status': 0})
#     else:
#         os.remove('{}/{}'.format(FUNC_ADDRESS, func_name))
#     return jsonify({'msg': '删除成功', 'status': 1})
