from flask import jsonify, request
from . import api, login_required
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/caseSet/add', methods=['POST'])
@login_required
def add_set():
    """ 添加用例集合 """
    data = request.json
    project_name = data.get('projectName')
    name = data.get('name')
    if not name:
        return jsonify({'msg': '用例集名称不能为空', 'status': 0})
    ids = data.get('id')
    project_id = Project.query.filter_by(name=project_name).first().id
    num = auto_num(data.get('num'), CaseSet, project_id=project_id)
    if ids:
        old_data = CaseSet.query.filter_by(id=ids).first()
        if CaseSet.query.filter_by(name=name, project_id=project_id).first() and name != old_data.name:
            return jsonify({'msg': '用例集名字重复', 'status': 0})
        old_data.name = name
        old_data.project_id = project_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if CaseSet.query.filter_by(name=name, project_id=project_id).first():
            return jsonify({'msg': '用例集名字重复', 'status': 0})
        else:
            new_set = CaseSet(name=name, project_id=project_id, num=num)
            db.session.add(new_set)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/caseSet/stick', methods=['POST'])
@login_required
def stick_set():
    """ 置顶用例集合 """
    data = request.json
    set_id = data.get('id')
    project_name = data.get('projectName')

    old_data = CaseSet.query.filter_by(id=set_id).first()
    old_num = old_data.num
    list_data = Project.query.filter_by(name=project_name).first().case_sets.all()
    num_sort(1, old_num, list_data, old_data)
    db.session.commit()
    return jsonify({'msg': '置顶完成', 'status': 1})


@api.route('/caseSet/find', methods=['POST'])
@login_required
def find_set():
    """ 查找用例集合 """
    data = request.json
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})

    all_sets = Project.query.filter_by(name=project_name).first().case_sets
    pagination = all_sets.paginate(page, per_page=per_page, error_out=False)
    _items = pagination.items
    total = pagination.total
    current_set = [{'label': s.name, 'id': s.id} for s in _items]
    all_set = [{'label': s.name, 'id': s.id} for s in all_sets.all()]
    return jsonify({'status': 1, 'total': total, 'data': current_set, 'all_set': all_set})


@api.route('/caseSet/edit', methods=['POST'])
@login_required
def edit_set():
    """ 返回待编辑用例集合 """
    data = request.json
    set_id = data.get('id')
    _edit = CaseSet.query.filter_by(id=set_id).first()
    _data = {'name': _edit.name, 'num': _edit.num}

    return jsonify({'data': _data, 'status': 1})


@api.route('/caseSet/del', methods=['POST'])
@login_required
def del_set():
    """ 删除用例集合 """
    data = request.json
    set_id = data.get('id')
    _edit = CaseSet.query.filter_by(id=set_id).first()
    case = Case.query.filter_by(case_set_id=set_id).first()
    if current_user.id != Project.query.filter_by(id=_edit.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的模块', 'status': 0})
    if case:
        return jsonify({'msg': '请先删除集合下的接口用例', 'status': 0})

    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})
