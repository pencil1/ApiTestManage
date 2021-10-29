from flask import jsonify, request
from . import api, login_required
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/module/find', methods=['POST'])
@login_required
def find_model():
    """ 查找接口模块 """
    data = request.json
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    project_id = data.get('projectId')
    if not project_id:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})

    # all_module = Project.get_first(id=project_id).modules
    all_module = Module.query.filter_by(project_id=project_id)
    pagination = all_module.paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [{'name': c.name, 'id': c.id, 'num': c.num} for c in items]

    # 查询出所有的接口模块是为了接口录入的时候可以选所有的模块
    _all_module = [{'name': s.name, 'id': s.id, 'num': s.num} for s in all_module.all()]
    return jsonify({'data': end_data, 'total': total, 'status': 1, 'all_module': _all_module})


@api.route('/module/add', methods=['POST'])
@login_required
def add_model():
    """ 接口模块增加、编辑 """
    data = request.json
    project_id = data.get('projectId')
    if not project_id:
        return jsonify({'msg': '请先创建项目', 'status': 0})
    name = data.get('name')
    if not name:
        return jsonify({'msg': '模块名称不能为空', 'status': 0})

    ids = data.get('id')
    num = auto_num(data.get('num'), Module, project_id=project_id)
    if ids:
        old_data = Module.get_first(id=ids)
        old_num = old_data.num
        list_data = Module.get_first(project_id=project_id).all()
        if Module.get_first(name=name, project_id=project_id) and name != old_data.name:
            return jsonify({'msg': '模块名字重复', 'status': 0})

        num_sort(num, old_num, list_data, old_data)
        old_data.name = name
        old_data.project_id = project_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Module.get_first(name=name, project_id=project_id):
            return jsonify({'msg': '模块名字重复', 'status': 0})
        else:
            new_model = Module(name=name, project_id=project_id, num=num)
            db.session.add(new_model)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/module/edit', methods=['POST'])
@login_required
def edit_model():
    """ 返回待编辑模块信息 """
    data = request.json
    ids = data.get('id')
    _edit = Module.get_first(id=ids)
    _data = {'gatherName': _edit.name, 'num': _edit.num}

    return jsonify({'data': _data, 'status': 1})


@api.route('/module/del', methods=['POST'])
@login_required
def del_model():
    """ 删除模块 """
    data = request.json
    ids = data.get('id')
    _edit = Module.get_first(id=ids)
    if current_user.id != Project.query.filter_by(id=_edit.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的模块', 'status': 0})
    if _edit.api_msg.all():
        return jsonify({'msg': '请先删除模块下的接口用例', 'status': 0})
    db.session.delete(_edit)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/module/stick', methods=['POST'])
@login_required
def stick_module():
    """ 置顶模块 """
    data = request.json
    module_id = data.get('id')
    project_id = data.get('projectId')
    old_data = Module.query.filter_by(id=module_id).first()
    old_num = old_data.num
    list_data = Module.query.filter_by(project_id=project_id).all()
    num_sort(1, old_num, list_data, old_data)
    db.session.commit()
    return jsonify({'msg': '置顶完成', 'status': 1})
