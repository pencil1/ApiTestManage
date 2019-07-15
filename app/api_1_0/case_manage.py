from flask import jsonify, request
from . import api, login_required
from app.models import *
from flask_login import current_user
from ..util.utils import *


@api.route('/case/add', methods=['POST'])
@login_required
def add_case():
    """ 用例添加、编辑 """
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'msg': '用例名称不能为空', 'status': 0})
    desc = data.get('desc')
    ids = data.get('ids')
    times = data.get('times')
    case_set_id = data.get('caseSetId')
    func_address = json.dumps(data.get('funcAddress'))
    project = data.get('project')
    project_data = Project.query.filter_by(name=project).first()
    project_id = project_data.id
    variable = data.get('variable')
    api_cases = data.get('apiCases')
    environment = data.get('environment')

    merge_variable = json.dumps(json.loads(variable) + json.loads(project_data.variables))
    _temp_check = extract_variables(convert(json.loads(merge_variable)))
    if not case_set_id:
        return jsonify({'msg': '请选择用例集', 'status': 0})
    if re.search('\${(.*?)}', '{}{}'.format(variable, json.dumps(api_cases)), flags=0) and not func_address:
        return jsonify({'msg': '参数引用函数后，必须引用函数文件', 'status': 0})
    if _temp_check:
        return jsonify({'msg': '参数引用${}在业务变量和项目公用变量均没找到'.format(',$'.join(_temp_check)), 'status': 0})

    cases_check = check_case(api_cases, func_address)
    # if cases_check:
    #     return jsonify({'msg': cases_check, 'status': 0})

    variable_check = check_case(variable, func_address)
    # if variable_check:
    #     return jsonify({'msg': variable_check, 'status': 0})

    num = auto_num(data.get('num'), Case, project_id=project_id, case_set_id=case_set_id)
    if ids:
        old_data = Case.query.filter_by(id=ids).first()
        old_num = old_data.num
        if Case.query.filter_by(name=name, project_id=project_id,
                                case_set_id=case_set_id).first() and name != old_data.name:
            return jsonify({'msg': '用例名字重复', 'status': 0})
        else:
            list_data = CaseSet.query.filter_by(id=case_set_id).first().cases.all()
            num_sort(num, old_num, list_data, old_data)
            old_data.name = name
            old_data.times = times
            old_data.project_id = project_id
            old_data.desc = desc
            old_data.environment = environment
            old_data.case_set_id = case_set_id
            old_data.func_address = func_address
            old_data.variable = variable
            db.session.commit()
        for _num, c in enumerate(api_cases):
            if c.get('id'):
                old_api_case = CaseData.query.filter_by(id=c.get('id')).first()
                old_api_case.num = _num
                old_api_case.extract = json.dumps(c['extract'])
                old_api_case.validate = json.dumps(c['validate'])
                old_api_case.variable = json.dumps(c['variable'])
                old_api_case.header = json.dumps(c['header'])
                old_api_case.json_variable = c['json_variable']
                old_api_case.param = json.dumps(c['param'])
                old_api_case.time = c['time']
                old_api_case.status_variables = json.dumps(c['statusCase']['variable'])
                old_api_case.status_extract = json.dumps(c['statusCase']['extract'])
                old_api_case.status_validate = json.dumps(c['statusCase']['validate'])
                old_api_case.status_param = json.dumps(c['statusCase']['param'])
                old_api_case.status_header = json.dumps(c['statusCase']['header'])
                old_api_case.name = c['case_name']
                old_api_case.status = json.dumps(c['status'])
                old_api_case.up_func = c['up_func']
                old_api_case.down_func = c['down_func']
                db.session.commit()
            else:
                new_api_case = CaseData(num=_num,
                                        json_variable=c['json_variable'],
                                        variable=json.dumps(c['variable']),
                                        extract=json.dumps(c['extract']),
                                        param=json.dumps(c['param']),
                                        validate=json.dumps(c['validate']),
                                        case_id=ids,
                                        time=c['time'],
                                        api_msg_id=c['apiMsgId'],
                                        status_variables=json.dumps(c['statusCase']['variable']),
                                        status_extract=json.dumps(c['statusCase']['extract']),
                                        status_validate=json.dumps(c['statusCase']['validate']),
                                        status_param=json.dumps(c['statusCase']['param']),
                                        header=json.dumps(c['header']),
                                        status_header=json.dumps(c['statusCase']['header']),
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

            new_case = Case(num=num, name=name, desc=desc, project_id=project_id, variable=variable,
                            func_address=func_address, case_set_id=case_set_id, times=times, environment=environment)
            db.session.add(new_case)
            db.session.commit()
            case_id = new_case.id
            for _num, c in enumerate(api_cases):
                new_api_case = CaseData(num=_num,
                                        variable=json.dumps(c['variable']),
                                        json_variable=c['json_variable'],
                                        extract=json.dumps(c['extract']),
                                        param=json.dumps(c['param']),
                                        time=c['time'],
                                        validate=json.dumps(c['validate']), case_id=case_id, api_msg_id=c['apiMsgId'],
                                        status_variables=json.dumps(c['statusCase']['variable']),
                                        status_extract=json.dumps(c['statusCase']['extract']),
                                        status_validate=json.dumps(c['statusCase']['validate']),
                                        status_param=json.dumps(c['statusCase']['param']),
                                        header=json.dumps(c['header']),
                                        status_header=json.dumps(c['statusCase']['header']),
                                        status=json.dumps(c['status']),
                                        name=c['case_name'], up_func=c['up_func'], down_func=c['down_func'])
                db.session.add(new_api_case)
                db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1, 'case_id': case_id})


@api.route('/case/find', methods=['POST'])
@login_required
def find_case():
    """ 查找用例 """
    data = request.json
    project_name = data.get('projectName')
    case_name = data.get('caseName')
    set_id = data.get('setId')
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    if not project_name:
        return jsonify({'msg': '请选择项目', 'status': 0})
    if case_name:
        cases = Case.query.filter_by(case_set_id=set_id).filter(Case.name.like('%{}%'.format(case_name))).all()
        total = len(cases)
        if not cases:
            return jsonify({'msg': '没有该用例', 'status': 0})
    else:
        cases = Case.query.filter_by(case_set_id=set_id)
        pagination = cases.order_by(Case.num.asc()).paginate(page, per_page=per_page, error_out=False)
        cases = pagination.items
        total = pagination.total
    cases = [{'num': c.num, 'name': c.name, 'label': c.name, 'leaf': True, 'desc': c.desc, 'sceneId': c.id,
              }
             for c in cases]
    return jsonify({'data': cases, 'total': total, 'status': 1})


@api.route('/case/del', methods=['POST'])
@login_required
def del_case():
    """ 删除用例 """
    data = request.json
    case_id = data.get('caseId')
    wait_del_case_data = Case.query.filter_by(id=case_id).first()
    if current_user.id != Project.query.filter_by(id=wait_del_case_data.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的用例', 'status': 0})

    _del_data = CaseData.query.filter_by(case_id=case_id).all()
    if _del_data:
        for d in _del_data:
            db.session.delete(d)
    db.session.delete(wait_del_case_data)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiCase/del', methods=['POST'])
@login_required
def del_api_case():
    """ 删除用例下的接口步骤信息 """
    data = request.json
    case_id = data.get('id')
    _data = CaseData.query.filter_by(id=case_id).first()
    db.session.delete(_data)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/case/edit', methods=['POST'])
@login_required
def edit_case():
    """ 返回待编辑用例信息 """
    data = request.json
    case_id = data.get('caseId')
    status = data.get('copyEditStatus')
    _data = Case.query.filter_by(id=case_id).first()
    cases = CaseData.query.filter_by(case_id=case_id).order_by(CaseData.num.asc()).all()
    case_data = []
    for case in cases:
        if status:
            case_id = ''
        else:
            case_id = case.id
        case_data.append({'num': case.num, 'name': ApiMsg.query.filter_by(id=case.api_msg_id).first().name,
                          'desc': ApiMsg.query.filter_by(id=case.api_msg_id).first().desc, 'apiMsgId': case.api_msg_id,
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
                          'header': json.loads(case.header),
                          'statusCase': {'variable': json.loads(case.status_variables),
                                         'extract': json.loads(case.status_extract),
                                         'validate': json.loads(case.status_validate),
                                         'param': json.loads(case.status_param),
                                         'header': json.loads(case.status_header),
                                         },
                          })
    _data2 = {'num': _data.num, 'name': _data.name, 'desc': _data.desc, 'cases': case_data, 'setId': _data.case_set_id,
              'func_address': json.loads(_data.func_address), 'times': _data.times, 'environment': _data.environment}
    if _data.variable:
        _data2['variable'] = json.loads(_data.variable)
    else:
        _data2['variable'] = []
    return jsonify({'data': _data2, 'status': 1})


@api.route('/config/data', methods=['POST'])
@login_required
def data_config():
    """ 返回需要配置信息 """
    data = request.json
    config_id = data.get('configId')
    _data = Config.query.filter_by(id=config_id).first()

    return jsonify({'data': {'variables': json.loads(_data.variables),
                             'func_address': json.loads(_data.func_address)},
                    'status': 1})
