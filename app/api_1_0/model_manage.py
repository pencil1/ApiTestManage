from flask import jsonify, request
from . import api
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/model/find', methods=['POST'])
def find_model():
    data = request.json
    model_name = data.get('modelName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})

    pro_id = Project.query.filter_by(name=project_name).first().id
    if model_name:
        model = Module.query.filter_by(project_id=pro_id).filter(Module.name.like('%{}%'.format(model_name))).all()
        if not model:
            return jsonify({'msg': '没有该模块', 'status': 0})
    else:
        model = Module.query.filter_by(project_id=pro_id)
        pagination = model.order_by(Module.id.asc()).paginate(page, per_page=per_page, error_out=False)
        model = pagination.items
        total = pagination.total

    model = [{'name': c.name, 'id': c.id, 'num': c.num} for c in model]
    return jsonify({'data': model, 'total': total, 'status': 1})


@api.route('/model/add', methods=['POST'])
def add_model():
    data = request.json
    project_name = data.get('projectName')
    gather_name = data.get('gatherName')
    ids = data.get('id')
    project_id = Project.query.filter_by(name=project_name).first().id

    num = auto_num(data.get('num'), Module, project_id=project_id)

    if ids:
        old_model_data = Module.query.filter_by(id=ids).first()
        if Module.query.filter_by(name=gather_name, project_id=project_id).first() \
                and gather_name != old_model_data.name:
            return jsonify({'msg': '模块名字重复', 'status': 0})

        elif Module.query.filter_by(num=num, project_id=project_id).first() \
                and num != old_model_data.num:
            return jsonify({'msg': '序号重复', 'status': 0})
        else:
            old_model_data.num = num
            old_model_data.name = gather_name
            old_model_data.project_id = project_id
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Module.query.filter_by(name=gather_name, project_id=project_id).first():
            return jsonify({'msg': '模块名字重复', 'status': 0})
        else:
            new_model = Module(name=gather_name, project_id=project_id, num=num)
            db.session.add(new_model)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/model/edit', methods=['POST'])
def edit_model():
    data = request.json
    model_id = data.get('id')
    _edit = Module.query.filter_by(id=model_id).first()
    _data = {'gatherName': _edit.name, 'num': _edit.num}

    return jsonify({'data': _data, 'status': 1})


@api.route('/model/del', methods=['POST'])
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
