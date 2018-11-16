from flask import jsonify, request
from flask_login import current_user
from app.models import *
from app.util.case_change.core import HarParser
from . import api
from ..util.http_run import RunCase
from ..util.utils import *


@api.route('/apiMsg/list', methods=['POST'])
def get_cases():
    data = request.json
    gat_name = data.get('gatName')
    gat_id = Module.query.filter_by(name=gat_name).first().id
    cases = ApiMsg.query.filter_by(module_id=gat_id).all()
    cases = [{'num': c.num, 'name': c.name, 'desc': c.desc, 'url': c.url} for c in cases]
    return jsonify({'data': cases, 'status': 1})


@api.route('/apiMsg/add', methods=['POST'])
def add_cases():
    data = request.json
    current_app.logger.info(data)
    project_name = data.get('projectName')
    api_msg_name = data.get('apiMsgName')
    if not api_msg_name:
        return jsonify({'msg': '接口名称不能为空', 'status': 0})
    variable_type = data.get('variableType')
    desc = data.get('desc')
    func_address = data.get('funcAddress')
    header = data.get('header')
    extract = data.get('extract')
    validate = data.get('validate')
    api_msg_id = data.get('apiMsgId')
    up_func = data.get('upFunc')
    down_func = data.get('downFunc')

    method = data.get('method')
    if method == -1:
        return jsonify({'msg': '请求方式不能为空', 'status': 0})

    module_id = data.get('moduleId')
    if not module_id and not project_name:
        return jsonify({'msg': '项目和模块不能为空', 'status': 0})

    url = data.get('url').split('?')[0]
    status_url = data.get('choiceUrl')
    if status_url == -1:
        if 'http' not in url:
            return jsonify({'msg': '基础url为空时，请补全api地址', 'status': 0})

    if not func_address and (data.get('upFunc') or data.get('downFunc')):
        return jsonify({'msg': '设置前后置函数后必须引用函数文件', 'status': 0})

    # if not url:
    #     return jsonify({'msg': '接口url不能为空', 'status': 0})
    # elif re.search('\${(.*?)}', url, flags=0) and not func_address:
    #     return jsonify({'msg': 'url引用函数后，基础信息处必须引用函数文件', 'status': 0})
    #
    variable = data.get('variable')
    json_variable = data.get('jsonVariable')
    param = data.get('param')
    # if re.search('\${(.*?)}', variable, flags=0) and not func_address:
    #     return jsonify({'msg': '参数引用函数后，基础信息处必须引用函数文件', 'status': 0})

    project_id = Project.query.filter_by(name=project_name).first().id
    # module_id = Module.query.filter_by(name=gather_name, project_id=project_id).first().id

    num = auto_num(data.get('num'), ApiMsg, module_id=module_id)

    if api_msg_id:
        old_api_msg_data = ApiMsg.query.filter_by(id=api_msg_id).first()
        old_num = old_api_msg_data.num
        if ApiMsg.query.filter_by(name=api_msg_name,
                                  module_id=module_id).first() and api_msg_name != old_api_msg_data.name:
            return jsonify({'msg': '接口名字重复', 'status': 0})

        # 当序号存在，且不是本来的序号，进入修改判断
        if ApiMsg.query.filter_by(num=num, module_id=module_id).first() and int(num) != old_num:
            num_sort(num, old_num, ApiMsg, module_id=module_id)
        else:
            old_api_msg_data.num = num

        old_api_msg_data.project_id = project_id
        old_api_msg_data.name = api_msg_name
        old_api_msg_data.validate = validate
        old_api_msg_data.func_address = func_address
        old_api_msg_data.up_func = up_func
        old_api_msg_data.down_func = down_func
        old_api_msg_data.desc = desc
        old_api_msg_data.status_url = status_url
        old_api_msg_data.variable_type = variable_type
        old_api_msg_data.method = method
        old_api_msg_data.url = url
        old_api_msg_data.header = header
        old_api_msg_data.variable = variable
        old_api_msg_data.json_variable = json_variable
        old_api_msg_data.param = param
        old_api_msg_data.extract = extract
        old_api_msg_data.module_id = module_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1, 'api_msg_id': api_msg_id, 'num': num})
    else:
        if ApiMsg.query.filter_by(name=api_msg_name, module_id=module_id).first():
            return jsonify({'msg': '接口名字重复', 'status': 0})
        else:
            new_cases = ApiMsg(name=api_msg_name, module_id=module_id, num=num, header=header,
                               status_url=status_url, func_address=func_address, up_func=up_func, project_id=project_id,
                               down_func=down_func, desc=desc, method=method, url=url, variable_type=variable_type,
                               param=param,
                               variable=variable,
                               json_variable=json_variable,
                               extract=extract,
                               validate=validate,
                               )
            db.session.add(new_cases)
            db.session.commit()
            _new = ApiMsg.query.filter_by(name=api_msg_name, module_id=module_id, project_id=project_id).first()
            _id = _new.id
            _num = _new.num
            return jsonify({'msg': '新建成功', 'status': 1, 'api_msg_id': _id, 'num': _num})


@api.route('/apiMsg/editAndCopy', methods=['POST'])
def edit_case():
    data = request.json
    case_id = data.get('apiMsgId')
    _edit = ApiMsg.query.filter_by(id=case_id).first()
    # variable = _edit.variable if _edit.variable_type == 'json' else json.loads(_edit.variable)

    _data = {'name': _edit.name, 'num': _edit.num, 'desc': _edit.desc, 'url': _edit.url,
             'method': _edit.method, 'funcAddress': _edit.func_address, 'status_url': int(_edit.status_url),
             'up_func': _edit.up_func, 'down_func': _edit.down_func,
             'variableType': _edit.variable_type,
             'param': json.loads(_edit.param),
             'header': json.loads(_edit.header),
             'variable': json.loads(_edit.variable),
             'json_variable': _edit.json_variable,
             'extract': json.loads(_edit.extract),
             'validate': json.loads(_edit.validate)}
    current_app.logger.info(_data)

    return jsonify({'data': _data, 'status': 1})


@api.route('/apiMsg/run', methods=['POST'])
def run_case():
    data = request.json
    api_msg_data = data.get('apiMsgData')
    suite_data = data.get('suiteData')
    project_name = data.get('projectName')
    config_id = data.get('configId')
    case_data_id = []
    if not api_msg_data and not suite_data:
        return jsonify({'msg': '请勾选信息后，再进行测试', 'status': 0})
    # 前端传入的数据不是按照编号来的，所以这里重新排序
    if api_msg_data:
        case_data_id = [(item['num'], item['apiMsgId']) for item in api_msg_data]
        case_data_id.sort(key=lambda x: x[0])

        api_msg = [ApiMsg.query.filter_by(id=c[1]).first() for c in case_data_id]
    if suite_data:
        for suite in suite_data:
            case_data_id += json.loads(ApiSuite.query.filter_by(id=suite['id']).first().api_ids)
            api_msg = [ApiMsg.query.filter_by(id=c).first() for c in case_data_id]

    d = RunCase(project_names=project_name, api_data=api_msg, config_id=config_id)
    res = json.loads(d.run_case())
    return jsonify({'msg': '测试完成', 'data': res, 'status': 1})


@api.route('/apiMsg/find', methods=['POST'])
def find_cases():
    data = request.json
    module_id = data.get('moduleId')
    project_name = data.get('projectName')
    case_name = data.get('caseName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 20
    if not project_name:
        return jsonify({'msg': '请选择项目', 'status': 0})
    if not module_id:
        return jsonify({'msg': '请先创建{}项目下的模块'.format(project_name), 'status': 0})

    if case_name:
        cases = ApiMsg.query.filter_by(module_id=module_id).filter(ApiMsg.name.like('%{}%'.format(case_name))).all()
        if not cases:
            return jsonify({'msg': '没有该用例', 'status': 0})
    else:
        cases = ApiMsg.query.filter_by(module_id=module_id)
        pagination = cases.order_by(ApiMsg.num.asc()).paginate(page, per_page=per_page, error_out=False)
        cases = pagination.items
        total = pagination.total

    _case = []
    for c in cases:
        _case.append(
            {'num': c.num, 'name': c.name, 'desc': c.desc, 'url': c.url, 'apiMsgId': c.id, 'gather_id': c.module_id,
             'variableType': c.variable_type,
             'variable': json.loads(c.variable),
             'json_variable': c.json_variable,
             'extract': json.loads(c.extract),
             'validate': json.loads(c.validate),
             'param': json.loads(c.param),
             'statusCase': {'extract': [True, True], 'variable': [True, True],
                            'validate': [True, True], 'param': [True, True]},
             'status': True, 'case_name': c.name, 'down_func': c.down_func, 'up_func': c.up_func, 'time': 1})
    return jsonify({'data': _case, 'total': total, 'status': 1})


@api.route('/apiMsg/del', methods=['POST'])
def del_cases():
    data = request.json
    api_msg_id = data.get('apiMsgId')
    _edit = ApiMsg.query.filter_by(id=api_msg_id).first()

    project_id = Module.query.filter_by(id=_edit.module_id).first().project_id
    if current_user.id != Project.query.filter_by(id=project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的接口', 'status': 0})

    del_case = CaseData.query.filter_by(api_msg_id=api_msg_id).all()
    for d in del_case:
        if d:
            db.session.delete(d)

    db.session.delete(_edit)

    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiMsg/fileChange', methods=['POST'])
def file_change():
    data = request.json
    project_name = data.get('projectName')
    module_id = data.get('moduleId')
    if not module_id and not project_name:
        return jsonify({'msg': '项目和模块不能为空', 'status': 0})
    import_format = data.get('importFormat')
    if not import_format:
        return jsonify({'msg': '请选择文件格式', 'status': 0})

    import_format = 'har' if import_format == 'HAR' else 'json'
    project_data = Project.query.filter_by(name=project_name).first()
    host = [project_data.host, project_data.host_two, project_data.host_three, project_data.host_four]

    import_api_address = data.get('importApiAddress')
    if not import_api_address:
        return jsonify({'msg': '请上传文件', 'status': 0})
    har_parser = HarParser(import_api_address, import_format)
    case_num = auto_num(data.get('caseNum'), ApiMsg, module_id=module_id)
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
