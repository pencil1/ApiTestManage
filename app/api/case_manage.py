from flask import jsonify, request
from flask_login import current_user

from app.models import *
from app.util.case_change.core import HarParser, postman_parser
from . import api
from ..util.http_run import RunCase
from ..util.utils import *


@api.route('/proGather/list')
def get_pro_gather():
    # if current_user.id == 4:
    _pros = Project.query.all()
    _pros2 = Project.query.filter_by(user_id=current_user.id).first()
    # _pros = Project.query.all()
    # print(current_user.id)
    pro = {}
    pro_url = {}
    scene_config_lists = {}
    #   获取每个项目下的模块名字
    for p in _pros:
        modules = Module.query.filter_by(project_id=p.id).all()
        if modules:
            pro[p.name] = [_gat.name for _gat in modules]
        else:
            pro[p.name] = ['']

        config_list = SceneConfig.query.order_by(SceneConfig.num.asc()).filter_by(project_id=p.id).all()
        if config_list:
            scene_config_lists[p.name] = [_config_list.name for _config_list in config_list]
        else:
            scene_config_lists[p.name] = ['']

    # 获取每个项目下的业务集
    for p in _pros:
        pro_url[p.name] = []
        if p.host:
            pro_url[p.name].append(p.host)
        if p.host_two:
            pro_url[p.name].append(p.host_two)
        if p.host_three:
            pro_url[p.name].append(p.host_three)
        if p.host_four:
            pro_url[p.name].append(p.host_four)
    if _pros2:
        _pros2 = {_pros2.name: pro[_pros2.name]}
    return jsonify(
        {'data': pro, 'urlData': pro_url, 'status': 1, 'user_pro': _pros2, 'config_name_list': scene_config_lists})


@api.route('/cases/list', methods=['POST'])
def get_cases():
    data = request.json
    gat_name = data.get('gatName')
    gat_id = Module.query.filter_by(name=gat_name).first().id
    cases = ApiMsg.query.filter_by(module_id=gat_id).all()
    cases = [{'num': c.num, 'name': c.name, 'desc': c.desc, 'url': c.url} for c in cases]
    return jsonify({'data': cases, 'status': 1})


@api.route('/cases/add', methods=['POST'])
def add_cases():
    data = request.json
    project_name = data.get('projectName')
    case_name = data.get('caseName')
    variable_type = data.get('variableType')
    case_desc = data.get('caseDesc')
    func_address = data.get('funcAddress')
    case_header = data.get('caseHeader')
    case_extract = data.get('caseExtract')
    case_validate = data.get('caseValidate')
    case_id = data.get('caseId')
    up_func = json.dumps(data.get('upFunc').split(',')) if data.get('upFunc') else data.get('upFunc')
    down_func = json.dumps(data.get('downFunc').split(',')) if data.get('downFunc') else data.get('down_func')

    case_method = data.get('caseMethod')
    if case_method == -1:
        return jsonify({'msg': '请求方式不能为空', 'status': 0})

    gather_name = data.get('gatherName')
    if not gather_name and not project_name:
        return jsonify({'msg': '项目和模块不能为空', 'status': 0})

    status_url = data.get('choiceUrl')
    if status_url == -1:
        return jsonify({'msg': '基础url不能为空', 'status': 0})

    if not func_address and (data.get('upFunc') or data.get('downFunc')):
        return jsonify({'msg': '设置前后置函数后必须引用函数文件', 'status': 0})

    case_url = data.get('caseUrl')
    # if not case_url:
    #     return jsonify({'msg': '接口url不能为空', 'status': 0})
    # elif re.search('\${(.*?)}', case_url, flags=0) and not func_address:
    #     return jsonify({'msg': 'url引用函数后，基础信息处必须引用函数文件', 'status': 0})
    #
    case_variable = data.get('caseVariable')
    # if re.search('\${(.*?)}', case_variable, flags=0) and not func_address:
    #     return jsonify({'msg': '参数引用函数后，基础信息处必须引用函数文件', 'status': 0})

    project_id = Project.query.filter_by(name=project_name).first().id
    module_id = Module.query.filter_by(name=gather_name, project_id=project_id).first().id

    case_num = auto_num(data.get('caseNum'), ApiMsg, module_id=module_id)

    if case_id:
        old_case_data = ApiMsg.query.filter_by(id=case_id).first()
        old_num = old_case_data.num
        if ApiMsg.query.filter_by(name=case_name, module_id=module_id).first() and case_name != old_case_data.name:
            return jsonify({'msg': '接口名字重复', 'status': 0})

        # 当序号存在，且不是本来的序号，进入修改判断
        if ApiMsg.query.filter_by(num=case_num, module_id=module_id).first() and int(case_num) != old_num:
            num_sort(case_num, old_num, ApiMsg, module_id=module_id)
        else:
            old_case_data.num = case_num
        old_case_data.name = case_name
        old_case_data.validate = case_validate
        old_case_data.func_address = func_address
        old_case_data.up_func = up_func
        old_case_data.down_func = down_func
        old_case_data.desc = case_desc
        old_case_data.status_url = status_url
        old_case_data.variable_type = variable_type
        old_case_data.method = case_method
        old_case_data.url = case_url
        old_case_data.headers = case_header
        old_case_data.variables = case_variable
        old_case_data.extract = case_extract
        old_case_data.module_id = module_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if ApiMsg.query.filter_by(name=case_name, module_id=module_id).first():
            return jsonify({'msg': '接口名字重复', 'status': 0})

        elif ApiMsg.query.filter_by(num=case_num, module_id=module_id).first():
            return jsonify({'msg': '序号重复', 'status': 0})
        else:
            new_cases = ApiMsg(name=case_name, module_id=module_id, validate=case_validate, num=case_num,
                               status_url=status_url, func_address=func_address, up_func=up_func,
                               down_func=down_func, desc=case_desc, method=case_method,
                               url=case_url, headers=case_header, variable_type=variable_type,
                               variables=case_variable, extract=case_extract)
            db.session.add(new_cases)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/cases/edit', methods=['POST'])
def edit_case():
    data = request.json
    case_id = data.get('caseId')
    _edit = ApiMsg.query.filter_by(id=case_id).first()
    variable = _edit.variables if _edit.variable_type == 'json' else json.loads(_edit.variables)

    _data = {'caseName': _edit.name, 'caseNum': _edit.num, 'caseDesc': _edit.desc, 'caseUrl': _edit.url,
             'caseMethod': _edit.method, 'funcAddress': _edit.func_address, 'status_url': int(_edit.status_url),
             'variableType': _edit.variable_type,
             'caseHeader': json.loads(_edit.headers), 'caseVariable': variable,
             'caseExtract': json.loads(_edit.extract), 'caseValidate': json.loads(_edit.validate), }

    if _edit.up_func:
        _data['up_func'] = ','.join(json.loads(_edit.up_func))
    if _edit.down_func:
        _data['down_func'] = ','.join(json.loads(_edit.down_func))

    return jsonify({'data': _data, 'status': 1})


@api.route('/cases/copy', methods=['POST'])
def copy_case():
    data = request.json
    case_id = data.get('caseId')
    _edit = ApiMsg.query.filter_by(id=case_id).first()
    variable = _edit.variables if _edit.variable_type == 'json' else json.loads(_edit.variables)

    _data = {'caseName': _edit.name, 'caseNum': _edit.num, 'caseDesc': _edit.desc, 'caseUrl': _edit.url,
             'caseMethod': _edit.method, 'funcAddress': _edit.func_address, 'status_url': int(_edit.status_url),
             'variableType': _edit.variable_type,
             'caseHeader': json.loads(_edit.headers), 'caseVariable': variable,
             'caseExtract': json.loads(_edit.extract), 'caseValidate': json.loads(_edit.validate), }
    if _edit.up_func:
        _data['up_func'] = ','.join(json.loads(_edit.up_func))
    if _edit.down_func:
        _data['down_func'] = ','.join(json.loads(_edit.down_func))

    return jsonify({'data': _data, 'status': 1})


@api.route('/cases/run', methods=['POST'])
def run_case():
    data = request.json
    case_data = data.get('caseData')
    project_name = data.get('projectName')
    config_name = data.get('configName')
    if not case_data:
        return jsonify({'msg': '请勾选信息后，再进行测试', 'status': 0})
    # 前端传入的数据不是按照编号来的，所以这里重新排序
    case_data_id = [(item['num'], item['caseId']) for item in case_data]
    case_data_id.sort(key=lambda x: x[0])

    old_case_data = [ApiMsg.query.filter_by(id=c[1]).first() for c in case_data_id]
    d = RunCase(project_names=project_name, case_data=[config_name, old_case_data])
    res = json.loads(d.run_case())
    return jsonify({'msg': '测试完成', 'data': res, 'status': 1})


@api.route('/cases/find', methods=['POST'])
def find_cases():
    data = request.json
    gat_name = data.get('gatName')
    project_name = data.get('projectName')
    case_name = data.get('caseName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    if not gat_name:
        return jsonify({'msg': '请先创建{}项目下的模块'.format(project_name), 'status': 0})

    gat_id = Module.query.filter_by(name=gat_name,
                                    project_id=Project.query.filter_by(name=project_name).first().id).first().id

    if case_name:
        cases = ApiMsg.query.filter_by(module_id=gat_id).filter(ApiMsg.name.like('%{}%'.format(case_name))).all()
        if not cases:
            return jsonify({'msg': '没有该用例', 'status': 0})
    else:
        cases = ApiMsg.query.filter_by(module_id=gat_id)
        pagination = cases.order_by(ApiMsg.num.asc()).paginate(page, per_page=per_page, error_out=False)
        cases = pagination.items
        total = pagination.total

    _case = []
    for c in cases:
        if c.variable_type == 'json':
            variable = c.variables
        else:
            variable = json.loads(c.variables)
        _case.append(
            {'num': c.num, 'name': c.name, 'desc': c.desc, 'url': c.url, 'caseId': c.id, 'gather_id': c.module_id,
             'variableType': c.variable_type,
             'variables': variable, 'extract': json.loads(c.extract),
             'validate': json.loads(c.validate),
             'statusCase': {'extract': [True, True], 'variable': [True, True], 'validate': [True, True]},
             'status': True, 'case_name': c.name, 'down_func':'', 'up_func':''})
    return jsonify({'data': _case, 'total': total, 'status': 1})


@api.route('/cases/del', methods=['POST'])
def del_cases():
    data = request.json
    case_id = data.get('caseId')
    _edit = ApiMsg.query.filter_by(id=case_id).first()

    project_id = Module.query.filter_by(id=_edit.module_id).first().project_id
    if current_user.id != Project.query.filter_by(id=project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的接口', 'status': 0})
    db.session.delete(_edit)
    del_case = ApiCase.query.filter_by(apiMsg_id=case_id).all()
    for d in del_case:
        db.session.delete(d)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/cases/fileChange', methods=['POST'])
def file_change():
    data = request.json
    project_name = data.get('projectName')
    gather_name = data.get('gatherName')
    if not gather_name and not project_name:
        return jsonify({'msg': '项目和模块不能为空', 'status': 0})
    import_format = data.get('importFormat')
    if not import_format:
        return jsonify({'msg': '请选择文件格式', 'status': 0})

    import_format = 'har' if import_format == 'HAR' else 'json'
    project_data = Project.query.filter_by(name=project_name).first()
    host = [project_data.host, project_data.host_two, project_data.host_three, project_data.host_four]
    project_id = project_data.id
    module_id = Module.query.filter_by(name=gather_name, project_id=project_id).first().id

    import_api_address = data.get('importApiAddress')
    if not import_api_address:
        return jsonify({'msg': '请上传文件', 'status': 0})
    har_parser = HarParser(import_api_address, import_format)
    case_num = auto_num(data.get('caseNum'), ApiMsg, module_id=module_id)
    # har_parser = postman_parser(import_api_address)
    # for msg in har_parser:
    for msg in har_parser.testset:
        # status_url = msg['test']['url'].replace(msg['test']['name'], '')
        # msg['test']['url'] = msg['test']['name']
        # print(msg['test']['status_url'])
        for h in host:
            if msg['status_url'] in h:
                msg['status_url'] = host.index(h)
                break
        else:
            msg['status_url'] = '0'
        new_case = ApiMsg(module_id=module_id, num=case_num, **msg)
        db.session.add(new_case)
        db.session.commit()
        case_num += 1

    return jsonify({'msg': '导入成功', 'status': 1})

#
# @api.route('/cases/del1', methods=['POST'])
# def del_cases1():
#     data = request.json
#     _edit = ApiMsg.query.filter_by().all()
#     for a in _edit:
#         if json.loads(a.variables):
#             if a.variable_type == 'data':
#                 a1 = json.loads(a.variables)
#                 for num, a2 in enumerate(a1):
#                     a1[num]['param_type'] = 'string'
#                 a.variables = json.dumps(a1)
#                 db.session.commit()
#
#     return jsonify({'msg': '删除成功', 'status': 1})
