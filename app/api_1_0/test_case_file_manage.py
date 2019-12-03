from flask import jsonify, request
from . import api, login_required
from app.models import *
from flask_login import current_user
from ..util.utils import *
from ..util.global_variable import *
import json


@api.route('/testCaseFile/add', methods=['POST'])
@login_required
def add_test_case_file():
    """ 添加用例集合 """
    data = request.json
    name = data.get('name')
    higher_id = data.get('higherId')
    status = data.get('status')
    ids = data.get('id')
    if not name:
        return jsonify({'msg': '名称不能为空', 'status': 0})
    num = auto_num(data.get('num'), CaseSet)
    if ids:
        old_data = TestCaseFile.query.filter_by(id=ids).first()
        old_data.name = name
        old_data.num = num
        old_data.higher_id = higher_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:

        _new = TestCaseFile(name=name, higher_id=higher_id, num=num, status=status, user_id=current_user.id)
        db.session.add(_new)
        db.session.commit()
        if status == 1:
            with open('{}{}.txt'.format(TEST_FILE_ADDRESS, _new.id), 'w', encoding='utf-8') as f:
                f.write(
                    """{"root":{"data":{"id":"byqb16f7t8o0","created":1574819812654,"text":"中心主题","priority":null,"font-family":"黑体, SimHei","font-size":32,"progress":null},"children":[]},"template":"right","theme":"fresh-blue","version":"1.4.43"}""")
        return jsonify({'msg': '新建成功', 'status': 1, 'id': _new.id, 'higher_id': _new.higher_id, })


#
@api.route('/testCaseFile/find', methods=['POST'])
@login_required
def find_test_case_file():
    """ 查找所有测试用例 """
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
                    TestCaseFile.query.filter_by(**kwargs).order_by(TestCaseFile.num.asc()).all())
            return _d

    end_data = get_data(TestCaseFile.query.filter_by(**kwargs).order_by(TestCaseFile.num.asc()).all())

    return jsonify({'status': 1, 'data': end_data, 'msg': 1})


@api.route('/testCaseFile/get', methods=['POST'])
@login_required
def get_test_case_file():
    """ 返回待编辑用例集合 """
    data = request.json
    ids = data.get('id')
    with open('{}{}.txt'.format(TEST_FILE_ADDRESS, ids), 'r', encoding='utf-8') as f:
        _data = f.read()
    return jsonify({'data': _data, 'status': 1})


@api.route('/testCaseFile/save', methods=['POST'])
@login_required
def save_test_case_file():
    """ 返回待编辑用例集合 """
    data = request.json
    _data = data.get('data')
    show = data.get('show')
    ids = data.get('ids')
    with open('{}{}.txt'.format(TEST_FILE_ADDRESS, ids), 'w', encoding='utf-8') as f:
        f.write(_data)
    if show:
        return jsonify({'status': 1, 'msg': '保存成功'})
    else:
        return jsonify({'status': 1})


#
@api.route('/testCaseFile/del', methods=['POST'])
@login_required
def del_test_case_file():
    """ 删除用例集合 """
    data = request.json
    ids = data.get('id')
    _edit = TestCaseFile.query.filter_by(id=ids).first()
    case = TestCaseFile.query.filter_by(higher_id=ids).first()
    print(current_user.id)
    print(_edit.user_id)
    if current_user.id != _edit.user_id:
        print(2234)
        return jsonify({'msg': '不能删除别人创建的', 'status': 0})
    if case:
        return jsonify({'msg': '请先删除该文件的下级内容', 'status': 0})

    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})
