from flask import jsonify, request
from . import api, login_required
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/apiSet/find', methods=['POST'])
@login_required
def find_api_set():
    """ 查找接口模块 """
    data = request.json
    # page = data.get('page') if data.get('page') else 1
    # per_page = data.get('sizePage') if data.get('sizePage') else 10
    project_id = data.get('projectId')
    if not project_id:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})

    def get_data(all_data):
        if not all_data:
            return
        if isinstance(all_data, list):
            if all_data:
                _t = []
                for d in all_data:
                    _t.append(get_data(d))
                return _t
            else:
                return []
        else:
            _d = {'id': all_data.id, 'num': all_data.num, 'name': all_data.name, 'project_id': all_data.project_id,
                  'higherId': all_data.higher_id,
                  'children': get_data(ApiSet.query.filter_by(higher_id=all_data.id, project_id=project_id).order_by(
                      ApiSet.num.asc()).all())}
            return _d

    end_data = get_data(ApiSet.query.filter_by(higher_id=0, project_id=project_id).order_by(ApiSet.num.asc()).all())
    return jsonify({'data': end_data, 'status': 1})


@api.route('/apiSet/add', methods=['POST'])
@login_required
def add_api_set():
    """ 接口模块增加、编辑 """
    data = request.json
    project_id = data.get('projectId')
    higher_id = data.get('higherId')
    if not project_id:
        return jsonify({'msg': '请先创建项目', 'status': 0})
    name = data.get('name')
    if not name:
        return jsonify({'msg': '集合名称不能为空', 'status': 0})

    ids = data.get('id')
    num = auto_num(data.get('num'), ApiSet, project_id=project_id, higher_id=higher_id)
    if ids:
        old_data = ApiSet.query.filter_by(id=ids).first()
        old_num = old_data.num
        if ApiSet.get_first(name=name, project_id=project_id) and name != old_data.name:
            return jsonify({'msg': '集合名字重复', 'status': 0})

        list_data = ApiSet.query.filter_by(project_id=project_id, higher_id=higher_id).all()
        num_sort(num, old_num, list_data, old_data)
        old_data.name = name
        old_data.project_id = project_id
        old_data.higher_id = higher_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:

        if ApiSet.get_first(name=name, project_id=project_id):
            return jsonify({'msg': '模块名字重复', 'status': 0})
        else:
            new_api_set = ApiSet(name=name, higher_id=higher_id, project_id=project_id, num=num)
            db.session.add(new_api_set)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/apiSet/edit', methods=['POST'])
@login_required
def edit_api_set():
    """ 返回待编辑模块信息 """
    data = request.json
    ids = data.get('id')
    _edit = ApiSet.get_first(id=ids)
    _data = {'gatherName': _edit.name, 'num': _edit.num}
    return jsonify({'data': _data, 'status': 1})


@api.route('/apiSet/del', methods=['POST'])
@login_required
def del_api_set():
    """ 删除模块 """
    data = request.json
    ids = data.get('id')
    _edit = ApiSet.get_first(id=ids)
    if current_user.id != Project.query.filter_by(id=_edit.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的模块', 'status': 0})
    if _edit.api_msg.all():
        return jsonify({'msg': '请先删除模块下的接口用例', 'status': 0})
    db.session.delete(_edit)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiSet/stick', methods=['POST'])
@login_required
def stick_api_set():
    """ 置顶模块 """
    data = request.json
    api_set_id = data.get('id')
    project_id = data.get('projectId')
    old_data = ApiSet.query.filter_by(id=api_set_id).first()
    old_num = old_data.num
    list_data = ApiSet.query.filter_by(project_id=project_id).all()
    num_sort(1, old_num, list_data, old_data)
    db.session.commit()
    return jsonify({'msg': '置顶完成', 'status': 1})
