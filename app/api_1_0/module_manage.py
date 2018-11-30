from flask import jsonify, request
from . import api
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/module/find', methods=['POST'])
def find_model():
    data = request.json
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})

    pro_d = Project.query.filter_by(name=project_name).first()
    p = pro_d.modules.paginate(page, per_page=per_page, error_out=False)
    print(p)
    pro_id = Project.query.filter_by(name=project_name).first().id
    all_module = Module.query.filter_by(project_id=pro_id)
    pagination = all_module.order_by(Module.num.asc()).paginate(page, per_page=per_page, error_out=False)
    my_module = pagination.items
    total = pagination.total

    my_module = [{'name': c.name, 'moduleId': c.id, 'num': c.num} for c in my_module]
    _all_module = [{'name': s.name, 'moduleId': s.id, 'num': s.num} for s in all_module.all()]
    return jsonify({'data': my_module, 'total': total, 'status': 1, 'all_module': _all_module})


@api.route('/module/add', methods=['POST'])
def add_model():
    data = request.json
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建项目', 'status': 0})
    name = data.get('name')
    ids = data.get('id')
    project_id = Project.query.filter_by(name=project_name).first().id

    num = auto_num(data.get('num'), Module, project_id=project_id)

    if ids:
        old_model_data = Module.query.filter_by(id=ids).first()
        if Module.query.filter_by(name=name, project_id=project_id).first() \
                and name != old_model_data.name:
            return jsonify({'msg': '模块名字重复', 'status': 0})

        elif Module.query.filter_by(num=num, project_id=project_id).first() \
                and num != old_model_data.num:
            return jsonify({'msg': '序号重复', 'status': 0})
        else:
            old_model_data.num = num
            old_model_data.name = name
            old_model_data.project_id = project_id
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Module.query.filter_by(name=name, project_id=project_id).first():
            return jsonify({'msg': '模块名字重复', 'status': 0})
        else:
            new_model = Module(name=name, project_id=project_id, num=num)
            db.session.add(new_model)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/module/edit', methods=['POST'])
def edit_model():
    data = request.json
    model_id = data.get('id')
    _edit = Module.query.filter_by(id=model_id).first()
    _data = {'gatherName': _edit.name, 'num': _edit.num}

    return jsonify({'data': _data, 'status': 1})


@api.route('/module/del', methods=['POST'])
def del_model():
    data = request.json
    ids = data.get('id')
    _edit = Module.query.filter_by(id=ids).first()
    case = ApiMsg.query.filter_by(module_id=_edit.id).first()
    if current_user.id != Project.query.filter_by(id=_edit.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的模块', 'status': 0})
    if case:
        return jsonify({'msg': '请先删除模块下的接口用例', 'status': 0})

    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/module/stick', methods=['POST'])
def stick_module():
    data = request.json
    module_id = data.get('id')
    project_name = data.get('projectName')
    project_id = Project.query.filter_by(name=project_name).first().id
    _data = Module.query.filter_by(id=module_id).first()
    num_sort('1', _data.num, Module, project_id=project_id)
    db.session.commit()

    return jsonify({'msg': '置顶完成', 'status': 1})
