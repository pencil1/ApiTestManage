from flask import jsonify, request
from flask_login import current_user
from app.models import *
from app.util.case_change.core import HarParser
from . import api, login_required
from ..util.http_run import RunCase
from ..util.utils import *


@api.route('/apiMsg/add', methods=['POST'])
@login_required
def add_api_msg():
    """ 接口信息增加、编辑 """
    data = request.json
    project_name = data.get('projectName')
    api_msg_name = data.get('apiMsgName')
    variable_type = data.get('variableType')
    desc = data.get('desc')
    header = data.get('header')
    extract = data.get('extract')
    validate = data.get('validate')
    api_msg_id = data.get('apiMsgId')
    up_func = data.get('upFunc')
    down_func = data.get('downFunc')
    method = data.get('method')
    module_id = data.get('moduleId')
    url = data.get('url').split('?')[0]
    status_url = data.get('choiceUrl')
    variable = data.get('variable')
    json_variable = data.get('jsonVariable')
    param = data.get('param')
    if not project_name:
        return jsonify({'msg': '项目不能为空', 'status': 0})
    if not module_id:
        return jsonify({'msg': '接口模块不能为空', 'status': 0})
    if not api_msg_name:
        return jsonify({'msg': '接口名称不能为空', 'status': 0})
    if method == -1:
        return jsonify({'msg': '请求方式不能为空', 'status': 0})
    if not url:
        return jsonify({'msg': '接口url不能为空', 'status': 0})
    if status_url == -1:
        if 'http' not in url:
            return jsonify({'msg': '基础url为空时，请补全api地址', 'status': 0})

    project_id = Project.query.filter_by(name=project_name).first().id
    num = auto_num(data.get('num'), ApiMsg, module_id=module_id)

    if api_msg_id:
        old_data = ApiMsg.query.filter_by(id=api_msg_id).first()
        old_num = old_data.num
        if ApiMsg.query.filter_by(name=api_msg_name, module_id=module_id).first() and api_msg_name != old_data.name:
            return jsonify({'msg': '接口名字重复', 'status': 0})

        list_data = Module.query.filter_by(id=module_id).first().api_msg.all()
        num_sort(num, old_num, list_data, old_data)
        old_data.project_id = project_id
        old_data.name = api_msg_name
        old_data.validate = validate
        old_data.up_func = up_func
        old_data.down_func = down_func
        old_data.desc = desc
        old_data.status_url = status_url
        old_data.variable_type = variable_type
        old_data.method = method
        old_data.url = url
        old_data.header = header
        old_data.variable = variable
        old_data.json_variable = json_variable
        old_data.param = param
        old_data.extract = extract
        old_data.module_id = module_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1, 'api_msg_id': api_msg_id, 'num': num})
    else:
        if ApiMsg.query.filter_by(name=api_msg_name, module_id=module_id).first():
            return jsonify({'msg': '接口名字重复', 'status': 0})
        else:
            new_cases = ApiMsg(name=api_msg_name,
                               num=num,
                               header=header,
                               up_func=up_func,
                               down_func=down_func,
                               url=url,
                               desc=desc,
                               param=param,
                               method=method,
                               variable=variable,
                               validate=validate,
                               project_id=project_id,
                               module_id=module_id,
                               status_url=status_url,
                               variable_type=variable_type,
                               json_variable=json_variable,
                               extract=extract, )
            db.session.add(new_cases)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1, 'api_msg_id': new_cases.id, 'num': new_cases.num})


@api.route('/apiMsg/editAndCopy', methods=['POST'])
@login_required
def edit_api_msg():
    """ 返回待编辑或复制的接口信息 """
    data = request.json
    case_id = data.get('apiMsgId')
    _edit = ApiMsg.query.filter_by(id=case_id).first()
    _data = {'name': _edit.name, 'num': _edit.num, 'desc': _edit.desc, 'url': _edit.url,
             'method': _edit.method, 'status_url': int(_edit.status_url),
             'up_func': _edit.up_func, 'down_func': _edit.down_func,
             'variableType': _edit.variable_type,
             'param': json.loads(_edit.param),
             'header': json.loads(_edit.header),
             'variable': json.loads(_edit.variable),
             'json_variable': _edit.json_variable,
             'extract': json.loads(_edit.extract),
             'validate': json.loads(_edit.validate)}
    return jsonify({'data': _data, 'status': 1})


@api.route('/apiMsg/run', methods=['POST'])
@login_required
def run_api_msg():
    """ 跑接口信息 """
    data = request.json
    api_msg_data = data.get('apiMsgData')
    project_name = data.get('projectName')
    config_id = data.get('configId')
    if not api_msg_data:
        return jsonify({'msg': '请勾选信息后，再进行测试', 'status': 0})

    # 前端传入的数据不是按照编号来的，所以这里重新排序
    api_ids = [(item['num'], item['apiMsgId']) for item in api_msg_data]
    api_ids.sort(key=lambda x: x[0])
    # api_data = [ApiMsg.query.filter_by(id=c[1]).first() for c in api_ids]
    api_ids = [c[1] for c in api_ids]

    project_id = Project.query.filter_by(name=project_name).first().id
    d = RunCase(project_id)
    d.get_api_test(api_ids, config_id)
    res = json.loads(d.run_case())

    return jsonify({'msg': '测试完成', 'data': res, 'status': 1})


@api.route('/apiMsg/find', methods=['POST'])
@login_required
def find_api_msg():
    """ 查接口信息 """
    data = request.json
    module_id = data.get('moduleId')
    project_name = data.get('projectName')
    api_name = data.get('apiName')
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 20
    if not project_name:
        return jsonify({'msg': '请选择项目', 'status': 0})
    if not module_id:
        return jsonify({'msg': '请先创建{}项目下的模块'.format(project_name), 'status': 0})

    if api_name:
        api_data = ApiMsg.query.filter_by(module_id=module_id).filter(ApiMsg.name.like('%{}%'.format(api_name)))
        # total = len(api_data)
        if not api_data:
            return jsonify({'msg': '没有该接口信息', 'status': 0})
    else:
        api_data = ApiMsg.query.filter_by(module_id=module_id)

    pagination = api_data.order_by(ApiMsg.num.asc()).paginate(page, per_page=per_page, error_out=False)
    api_data = pagination.items
    total = pagination.total
    _api = [{'num': c.num,
             'name': c.name,
             'desc': c.desc,
             'url': c.url,
             'apiMsgId': c.id,
             'gather_id': c.module_id,
             'variableType': c.variable_type,
             'variable': json.loads(c.variable),
             'json_variable': c.json_variable,
             'extract': json.loads(c.extract),
             'validate': json.loads(c.validate),
             'param': json.loads(c.param),
             'header': json.loads(c.header),
             'statusCase': {'extract': [True, True], 'variable': [True, True],
                            'validate': [True, True], 'param': [True, True], 'header': [True, True]},
             'status': True, 'case_name': c.name, 'down_func': c.down_func, 'up_func': c.up_func, 'time': 1}
            for c in api_data]
    return jsonify({'data': _api, 'total': total, 'status': 1})


@api.route('/apiMsg/del', methods=['POST'])
@login_required
def del_api_msg():
    """ 删除接口信息 """
    data = request.json
    api_msg_id = data.get('apiMsgId')
    _data = ApiMsg.query.filter_by(id=api_msg_id).first()

    project_id = Module.query.filter_by(id=_data.module_id).first().project_id
    if current_user.id != Project.query.filter_by(id=project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的接口', 'status': 0})

    # 同步删除接口信息下对应用例下的接口步骤信息
    for d in CaseData.query.filter_by(api_msg_id=api_msg_id).all():
        db.session.delete(d)

    db.session.delete(_data)

    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiMsg/fileChange', methods=['POST'])
@login_required
def file_change():
    """ 导入接口信息 """
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
    host = json.loads(project_data.host)

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
        new_case = ApiMsg(project_id=project_data.id, module_id=module_id, num=case_num, **msg)
        db.session.add(new_case)
        db.session.commit()
        case_num += 1
    return jsonify({'msg': '导入成功', 'status': 1})
