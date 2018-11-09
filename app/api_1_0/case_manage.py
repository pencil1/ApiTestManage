from flask import jsonify, request
from . import api
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/case/add', methods=['POST'])
def add_case():
    data = request.json
    name = data.get('name')
    desc = data.get('desc')
    ids = data.get('ids')
    times = data.get('times')
    case_set_id = data.get('caseSetId')
    if not case_set_id:
        return jsonify({'msg': '请选择用例集', 'status': 0})
    func_address = data.get('funcAddress')
    project = data.get('project')
    project_data = Project.query.filter_by(name=project).first()
    project_id = project_data.id
    num = auto_num(data.get('num'), Case, project_id=project_id, case_set_id=case_set_id)
    variable = data.get('variable')

    api_cases = data.get('apiCases')

    merge_variable = json.dumps(json.loads(variable) + json.loads(project_data.variables))
    _temp_check = extract_variables(convert(json.loads(merge_variable)))
    if _temp_check:
        return jsonify({'msg': '参数引用${}在业务变量和项目公用变量均没找到'.format(',$'.join(_temp_check)), 'status': 0})
    if re.search('\${(.*?)}', '{}{}'.format(variable, json.dumps(api_cases)), flags=0) and not func_address:
        return jsonify({'msg': '参数引用函数后，必须引用函数文件', 'status': 0})

    cases_check = check_case(api_cases, func_address)
    if cases_check:
        return jsonify({'msg': cases_check, 'status': 0})

    variable_check = check_case(variable, func_address)
    if variable_check:
        return jsonify({'msg': variable_check, 'status': 0})

    if ids:
        old_scene_data = Case.query.filter_by(id=ids).first()
        old_num = old_scene_data.num
        if Case.query.filter_by(name=name, project_id=project_id,
                                case_set_id=case_set_id).first() and name != old_scene_data.name:
            return jsonify({'msg': '用例名字重复', 'status': 0})
        elif Case.query.filter_by(num=num, project_id=project_id, case_set_id=case_set_id).first() and num != old_num:
            num_sort(num, old_num, Case, project_id=project_id, case_set_id=case_set_id)
        else:
            old_scene_data.num = num
        old_scene_data.name = name
        old_scene_data.times = times
        old_scene_data.project_id = project_id
        old_scene_data.desc = desc
        old_scene_data.case_set_id = case_set_id
        old_scene_data.func_address = func_address
        old_scene_data.variable = variable
        # old_scene_data.variable = json_variable
        db.session.commit()
        for num1, c in enumerate(api_cases):
            if c.get('id'):
                old_api_case = CaseData.query.filter_by(id=c.get('id')).first()
                old_api_case.num = num1

                old_api_case.extract = json.dumps(c['extract'])
                old_api_case.validate = json.dumps(c['validate'])
                old_api_case.variable = json.dumps(c['variable'])
                old_api_case.json_variable = c['json_variable']
                old_api_case.param = json.dumps(c['param'])
                old_api_case.time = c['time']
                old_api_case.status_variables = json.dumps(c['statusCase']['variable'])
                old_api_case.status_extract = json.dumps(c['statusCase']['extract'])
                old_api_case.status_validate = json.dumps(c['statusCase']['validate'])
                old_api_case.status_param = json.dumps(c['statusCase']['param'])
                old_api_case.name = c['case_name']
                old_api_case.status = json.dumps(c['status'])
                old_api_case.up_func = c['up_func']
                old_api_case.down_func = c['down_func']
                db.session.commit()
                # old_api_case.num = num1
            else:
                new_api_case = CaseData(num=num1,
                                        json_variable=c['json_variable'],
                                        variable=json.dumps(c['variable']),
                                        extract=json.dumps(c['extract']),
                                        param=json.dumps(c['param']),
                                        validate=json.dumps(c['validate']),

                                        case_id=ids, api_msg_id=c['apiMsgId'],
                                        status_variables=json.dumps(c['statusCase']['variable']),time=c['time'],
                                        status_extract=json.dumps(c['statusCase']['extract']),
                                        status_validate=json.dumps(c['statusCase']['validate']),
                                        status_param=json.dumps(c['statusCase']['param']),
                                        status=json.dumps(c['status']),
                                        name=c['case_name'], up_func=c['up_func'], down_func=c['down_func'])
                db.session.add(new_api_case)
                db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Case.query.filter_by(name=name, project_id=project_id, case_set_id=case_set_id).first():
            return jsonify({'msg': '用例名字重复', 'status': 0})
        elif Case.query.filter_by(num=num, project_id=project_id, case_set_id=case_set_id).first():
            return jsonify({'msg': '编号重复', 'status': 0})
        else:

            new_case = Case(num=num, name=name, desc=desc, project_id=project_id, variables=variable,
                            func_address=func_address, case_set_id=case_set_id, times=times)
            db.session.add(new_case)
            db.session.commit()
            case_id = Case.query.filter_by(name=name, project_id=project_id, case_set_id=case_set_id).first().id
            # case_id = Scene.query.filter_by(name=name, case_set_id=case_set_id).first().id
            for num1, c in enumerate(api_cases):
                if c['variableType'] == 'json':
                    variable = c['variable']
                else:
                    variable = json.dumps(c['variable'])
                # if c.statusCase
                new_api_case = CaseData(num=num1, variable=variable, extract=json.dumps(c['extract']),
                                        param=json.dumps(c['param']), time=c['time'],
                                        validate=json.dumps(c['validate']), case_id=case_id, api_msg_id=c['apiMsgId'],
                                        status_variables=json.dumps(c['statusCase']['variable']),
                                        status_extract=json.dumps(c['statusCase']['extract']),
                                        status_validate=json.dumps(c['statusCase']['validate']),
                                        status_param=json.dumps(c['statusCase']['param']),
                                        status=json.dumps(c['status']),
                                        name=c['case_name'], up_func=c['up_func'], down_func=c['down_func'])
                db.session.add(new_api_case)
                db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/case/find', methods=['POST'])
def find_scene():
    data = request.json
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})
    scene_name = data.get('sceneName')
    set_id = data.get('setId')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    if scene_name:
        cases = Case.query.filter_by(case_set_id=set_id).filter(Case.name.like('%{}%'.format(scene_name))).all()
        if not cases:
            return jsonify({'msg': '没有该用例', 'status': 0})
    else:
        cases = Case.query.filter_by(project_id=Project.query.filter_by(name=project_name).first().id,
                                     case_set_id=set_id)

        pagination = cases.order_by(Case.num.asc()).paginate(page, per_page=per_page, error_out=False)
        cases = pagination.items
        total = pagination.total
    cases = [{'num': c.num, 'name': c.name, 'label': c.name, 'leaf': True, 'desc': c.desc, 'sceneId': c.id} for c in
             cases]
    return jsonify({'data': cases, 'total': total, 'status': 1})


@api.route('/case/findOld', methods=['POST'])
def find_old_scene():
    data = request.json
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})
    scene_name = data.get('sceneName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    if scene_name:
        cases = Case.query.filter_by(case_set_id=None).filter(Case.name.like('%{}%'.format(scene_name))).all()
        if not cases:
            return jsonify({'msg': '没有该用例', 'status': 0})
    else:
        cases = Case.query.filter_by(project_id=Project.query.filter_by(name=project_name).first().id,
                                     case_set_id=None)

        pagination = cases.order_by(Case.num.asc()).paginate(page, per_page=per_page, error_out=False)
        cases = pagination.items
        total = pagination.total
    cases = [{'num': c.num, 'name': c.name, 'desc': c.desc, 'sceneId': c.id} for c in cases]
    return jsonify({'data': cases, 'total': total, 'status': 1})


@api.route('/case/del', methods=['POST'])
def del_scene():
    data = request.json
    case_id = data.get('caseId')
    _data = Case.query.filter_by(id=case_id).first()
    if current_user.id != Project.query.filter_by(id=_data.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的用例', 'status': 0})
    del_case = CaseData.query.filter_by(case_id=case_id).all()
    if del_case:
        for d in del_case:
            db.session.delete(d)

    db.session.delete(_data)

    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiCase/del', methods=['POST'])
def del_api_case():
    data = request.json
    case_id = data.get('id')
    _data = CaseData.query.filter_by(id=case_id).first()
    db.session.delete(_data)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/case/edit', methods=['POST'])
def edit_scene():
    data = request.json
    case_id = data.get('caseId')
    status = data.get('copyEditStatus')
    _data = Case.query.filter_by(id=case_id).first()

    cases = CaseData.query.filter_by(case_id=case_id).order_by(CaseData.num.asc()).all()
    case_data = []
    for case in cases:
        # if ApiMsg.query.filter_by(id=case.api_msg_id).first().variable_type == 'json':
        #     variable = case.variable
        # else:
        #     variable = json.loads(case.variable)

        if status:
            case_id = ''
        else:
            case_id = case.id
        case_data.append({'num': case.num, 'name': ApiMsg.query.filter_by(id=case.api_msg_id).first().name,
                          'desc': ApiMsg.query.filter_by(id=case.api_msg_id).first().desc, 'api_msg_id': case.api_msg_id,
                          'id': case_id,
                          'status': json.loads(case.status),
                          'variableType': ApiMsg.query.filter_by(id=case.api_msg_id).first().variable_type,
                          'case_name': case.name,
                          'time': case.time,
                          'up_func': case.up_func,
                          'down_func': case.down_func,
                          'variable': json.loads(case.variable),
                          'json_variable': case.json_variable,
                          'param': json.loads(case.param),
                          'extract': json.loads(case.extract),
                          'validate': json.loads(case.validate),
                          'statusCase': {'variable': json.loads(case.status_variables),
                                         'extract': json.loads(case.status_extract),
                                         'validate': json.loads(case.status_validate),
                                         'param': json.loads(case.status_param)},

                          })
    _data2 = {'num': _data.num, 'name': _data.name, 'desc': _data.desc, 'cases': case_data, 'setId': _data.case_set_id,
              'func_address': _data.func_address, 'times': _data.times}

    if _data.variable:
        _data2['variable'] = json.loads(_data.variable)
    else:
        _data2['variable'] = []

    return jsonify({'data': _data2, 'status': 1})


@api.route('/config/data', methods=['POST'])
def data_config():
    data = request.json
    config_id = data.get('configId')
    # _edit = SceneConfig.query.filter_by(name=name).first().variables
    _data = Config.query.filter_by(id=config_id).first()

    return jsonify({'data': {'variables': json.loads(_data.variables),
                             'func_address': _data.func_address},
                    'status': 1})
