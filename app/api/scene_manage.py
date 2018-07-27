import importlib
import json

import re
from flask import jsonify, request
from . import api
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/scene/add', methods=['POST'])
def add_scene():
    data = request.json
    name = data.get('name')
    desc = data.get('desc')
    ids = data.get('ids')
    func_address = data.get('funcAddress')
    project = data.get('project')
    project_data = Project.query.filter_by(name=project).first()
    project_id = project_data.id
    num = auto_num(data.get('num'), Scene, project_id=project_id)
    variable = data.get('variable')
    cases = data.get('cases')

    merge_variable = json.dumps(json.loads(variable) + json.loads(project_data.variables))
    _temp_check = extract_variables(convert(json.loads(merge_variable)))
    if _temp_check:
        return jsonify({'msg': '参数引用${}在业务变量和项目公用变量均没找到'.format(',$'.join(_temp_check)), 'status': 0})
    if re.search('\${(.*?)}', '{}{}'.format(variable, json.dumps(cases)), flags=0) and not func_address:
        return jsonify({'msg': '参数引用函数后，必须引用函数文件', 'status': 0})

    cases_check = check_case(cases, func_address)
    if cases_check:
        return jsonify({'msg': cases_check, 'status': 0})

    variable_check = check_case(variable, func_address)
    if variable_check:
        return jsonify({'msg': variable_check, 'status': 0})

    if ids:
        old_scene_data = Scene.query.filter_by(id=ids).first()
        old_num = old_scene_data.num
        if Scene.query.filter_by(name=name, project_id=project_id).first() and name != old_scene_data.name:
            return jsonify({'msg': '业务集名字重复', 'status': 0})
        elif Scene.query.filter_by(num=num, project_id=project_id).first() and num != old_num:
            num_sort(num, old_num, Scene, project_id=project_id)
        else:
            old_scene_data.num = num
        old_scene_data.name = name
        old_scene_data.project_id = project_id
        old_scene_data.desc = desc
        old_scene_data.func_address = func_address
        old_scene_data.variables = variable
        db.session.commit()
        for num1, c in enumerate(cases):
            if c.get('id'):
                old_api_case = ApiCase.query.filter_by(id=c.get('id')).first()
                old_api_case.num = num1

                old_api_case.extract = json.dumps(c['extract'])
                old_api_case.validate = json.dumps(c['validate'])
                old_api_case.status_variables = json.dumps(c['statusCase']['variable'])
                old_api_case.status_extract = json.dumps(c['statusCase']['extract'])
                old_api_case.status_validate = json.dumps(c['statusCase']['validate'])
                old_api_case.name = c['case_name']
                old_api_case.status = json.dumps(c['status'])
                old_api_case.up_func = c['up_func']
                old_api_case.down_func = c['down_func']
                if c['variableType'] == 'json':
                    variable = c['variables']
                else:
                    variable = json.dumps(c['variables'])
                old_api_case.variables = variable
                db.session.commit()
                # old_api_case.num = num1
            else:
                if c['variableType'] == 'json':
                    variable = c['variables']
                else:
                    variable = json.dumps(c['variables'])
                new_case = ApiCase(num=num1, variables=variable, extract=json.dumps(c['extract']),
                                   validate=json.dumps(c['validate']), scene_id=ids, apiMsg_id=c['caseId'],
                                   status_variables=json.dumps(c['statusCase']['variable']),
                                   status_extract=json.dumps(c['statusCase']['extract']),
                                   status_validate=json.dumps(c['statusCase']['validate']),
                                   status=json.dumps(c['status']),
                                   name=c['case_name'], up_func=c['up_func'], down_func=c['down_func'])
                db.session.add(new_case)
                db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Scene.query.filter_by(name=name).first():
            return jsonify({'msg': '业务名字重复', 'status': 0})
        elif Scene.query.filter_by(num=num, project_id=project_id).first():
            return jsonify({'msg': '编号重复', 'status': 0})
        else:

            new_scene = Scene(num=num, name=name, desc=desc, project_id=project_id, variables=variable,
                              func_address=func_address)
            db.session.add(new_scene)
            db.session.commit()
            scene_id = Scene.query.filter_by(name=name).first().id
            for num1, c in enumerate(cases):
                if c['variableType'] == 'json':
                    variable = c['variables']
                else:
                    variable = json.dumps(c['variables'])
                # if c.statusCase
                new_case = ApiCase(num=num1, variables=variable, extract=json.dumps(c['extract']),
                                   validate=json.dumps(c['validate']), scene_id=scene_id, apiMsg_id=c['caseId'],
                                   status_variables=json.dumps(c['statusCase']['variable']),
                                   status_extract=json.dumps(c['statusCase']['extract']),
                                   status_validate=json.dumps(c['statusCase']['validate']),
                                   status=json.dumps(c['status']),
                                   name=c['case_name'], up_func=c['up_func'], down_func=c['down_func'])
                db.session.add(new_case)
                db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/scene/find', methods=['POST'])
def find_scene():
    data = request.json
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})
    scene_name = data.get('sceneName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    if scene_name:
        cases = Scene.query.filter(Scene.name.like('%{}%'.format(scene_name))).all()
        if not cases:
            return jsonify({'data': '没有该用例', 'status': 0})
    else:
        cases = Scene.query.filter_by(project_id=Project.query.filter_by(name=project_name).first().id)
        pagination = cases.order_by(Scene.num.asc()).paginate(page, per_page=per_page, error_out=False)
        cases = pagination.items
        total = pagination.total
    cases = [{'num': c.num, 'name': c.name, 'desc': c.desc, 'sceneId': c.id} for c in cases]
    return jsonify({'data': cases, 'total': total, 'status': 1})


@api.route('/scene/del', methods=['POST'])
def del_scene():
    data = request.json
    scene_id = data.get('sceneId')
    _edit = Scene.query.filter_by(id=scene_id).first()
    if current_user.id != Project.query.filter_by(id=_edit.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的业务集', 'status': 0})
    db.session.delete(_edit)
    del_case = ApiCase.query.filter_by(scene_id=scene_id).all()
    if del_case:
        for d in del_case:
            db.session.delete(d)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiCase/del', methods=['POST'])
def del_api_case():
    data = request.json
    case_id = data.get('id')
    _edit = ApiCase.query.filter_by(id=case_id).first()
    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/scene/edit', methods=['POST'])
def edit_scene():
    data = request.json
    scene_id = data.get('sceneId')
    _edit = Scene.query.filter_by(id=scene_id).first()

    cases = ApiCase.query.filter_by(scene_id=scene_id).order_by(ApiCase.num.asc()).all()
    case_data = []
    for case in cases:
        if ApiMsg.query.filter_by(id=case.apiMsg_id).first().variable_type == 'json':
            variable = case.variables
        else:
            variable = json.loads(case.variables)
        case_data.append({'num': case.num, 'name': ApiMsg.query.filter_by(id=case.apiMsg_id).first().name,
                          'desc': ApiMsg.query.filter_by(id=case.apiMsg_id).first().desc, 'api_caseId': case.id,
                          'id': case.id,
                          'status': json.loads(case.status),
                          'variableType': ApiMsg.query.filter_by(id=case.apiMsg_id).first().variable_type,
                          'variables': variable,
                          'case_name': case.name,
                          'up_func': case.up_func,
                          'down_func': case.down_func,
                          'extract': json.loads(case.extract),
                          'validate': json.loads(case.validate),
                          'statusCase': {'variable': json.loads(case.status_variables),
                                         'extract': json.loads(case.status_extract),
                                         'validate': json.loads(case.status_validate)},
                          })
    _data = {'num': _edit.num, 'name': _edit.name, 'desc': _edit.desc, 'cases': case_data,
             'func_address': _edit.func_address}
    if _edit.variables:
        _data['variables'] = json.loads(_edit.variables)
    else:
        _data['variables'] = []

    return jsonify({'data': _data, 'status': 1})


@api.route('/config/data', methods=['POST'])
def data_config():
    data = request.json
    name = data.get('name')
    # _edit = SceneConfig.query.filter_by(name=name).first().variables
    _data = SceneConfig.query.filter_by(name=name).first()

    return jsonify({'data': {'variables': json.loads(_data.variables),
                             'func_address': _data.func_address},
                    'status': 1})
