import time

from flask import jsonify, request
from flask_login import current_user
from app.models import *
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, and_, or_
from . import api, login_required
from ..util.http_run import RunCase
from ..util.utils import *
from ..util.validators import parameter_validator
# from ..util.case_maker import gener


@api.route('/apiMsg/getTempSteps', methods=['POST'])
@login_required
def gen_cases():
    """ 根据某接口生成一系列测试用例  """
    data = request.json
    # return jsonify({'msg': '接口名字重复', 'status': 0})
    module_id = data.get('apiId')
    c = ApiMsg.query.filter_by(id=module_id).first()
    _simple = {
                  'name': c.name,
                  'method': c.method,
                  'variableType': c.variable_type,
                  'header': json.loads(c.header),
                  'param': json.loads(c.param),
                  'variable': json.loads(c.variable),
                  'json_variable': c.json_variable,
                  'swagger_json_variable': json.loads(
                      c.swagger_json_variable) if c.swagger_json_variable else None
              },
    current_app.logger.info(type(_simple))
    current_app.logger.info(json.dumps(_simple, ensure_ascii=False))

    if str(c.method).upper() == 'POST' and c.variable_type == 'json':
        end_data_list = gener.gen_cases(_simple[0])  # 接收字典返回列表
        current_app.logger.info(end_data_list)
        # print(type(end_data_list[0]))
        return jsonify([{'num': c.num,
                         'name': c.name,
                         'desc': c.desc,
                         'url': c.url,
                         'skip': c.skip,
                         'apiMsgId': c.id,
                         'method': c.method,
                         'api_set_id': c.api_set_id,
                         'variableType': c.variable_type,
                         'variable': json.loads(c.variable),
                         'json_variable': json.dumps(_data),
                         'extract': json.loads(c.extract),
                         'validate': json.loads(c.validate),
                         'param': json.loads(c.param),
                         'header': json.loads(c.header),
                         'parameters': '[]',
                         # 'check': False,
                         'statusCase': {'extract': [True, True], 'variable': [True, True],
                                        'validate': [True, True], 'param': [True, True],
                                        'header': [True, True], 'parameters': False},
                         'status': True, 'case_name': c.name, 'down_func': c.down_func, 'up_func': c.up_func, 'time': 1}
                        for _data in end_data_list])


@api.route('/apiMsg/add', methods=['POST'])
@login_required
def add_api_msg():
    """ 接口信息增加、编辑 """
    data = request.json
    variable_type = data.get('variableType')
    desc = data.get('desc')
    header = data.get('header')
    extract = data.get('extract')
    validate = data.get('validate')
    api_msg_id = data.get('apiMsgId')
    up_func = data.get('upFunc')
    down_func = data.get('downFunc')
    skip = data.get('skip')
    status_url = data.get('choiceUrl')
    variable = data.get('variable')
    json_variable = data.get('jsonVariable')
    swagger_json_variable = data.get('swaggerJsonVariable')
    param = data.get('param')
    project_id = parameter_validator(data.get('projectId'), msg='请先选择项目', status=0)
    api_set_id = parameter_validator(data.get('apiSetId'), msg='请先接口集合', status=0)
    api_msg_name = parameter_validator(data.get('apiMsgName'), msg='接口名称不能为空', status=0)
    method = parameter_validator(data.get('method'), msg='请求方式不能为空', status=0)
    url = parameter_validator(data.get('url').split('?')[0], msg='接口地址不能为空', status=0)
    if not isinstance(status_url, int):
        if 'http' not in url:
            return jsonify({'msg': '基础url为空时，请补全api地址', 'status': 0})
    num = auto_num(data.get('num'), ApiMsg, api_set_id=api_set_id)
    if api_msg_id:
        old_data = ApiMsg.query.filter_by(id=api_msg_id).first()
        old_num = old_data.num
        if ApiMsg.query.filter_by(name=api_msg_name, api_set_id=api_set_id).first() and api_msg_name != old_data.name:
            return jsonify({'msg': '接口名字重复', 'status': 0})

        list_data = ApiSet.query.filter_by(id=api_set_id).first().api_msg.all()
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
        old_data.skip = skip
        old_data.header = header
        old_data.variable = variable
        old_data.json_variable = json_variable
        old_data.swagger_json_variable = swagger_json_variable
        old_data.param = param
        old_data.extract = extract
        old_data.api_set_id = api_set_id
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1, 'api_msg_id': api_msg_id, 'num': num})
    else:
        if ApiMsg.query.filter_by(name=api_msg_name, api_set_id=api_set_id).first():
            return jsonify({'msg': '接口名字重复', 'status': 0})
        else:
            new_cases = ApiMsg(name=api_msg_name,
                               num=num,
                               header=header,
                               up_func=up_func,
                               down_func=down_func,
                               url=url,
                               skip=skip,
                               desc=desc,
                               param=param,
                               method=method,
                               variable=variable,
                               validate=validate,
                               project_id=project_id,
                               api_set_id=api_set_id,
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
    _data = {'name': _edit.name, 'num': _edit.num, 'desc': _edit.desc, 'url': _edit.url, 'skip': _edit.skip,
             'api_set_id': _edit.api_set_id,
             'method': _edit.method, 'status_url': int(_edit.status_url) if _edit.status_url else None,
             'up_func': _edit.up_func, 'down_func': _edit.down_func,
             'variableType': _edit.variable_type,
             'param': json.loads(_edit.param),
             'header': json.loads(_edit.header),
             'variable': json.loads(_edit.variable),
             'json_variable': _edit.json_variable,
             'swagger_json_variable': _edit.swagger_json_variable,
             'extract': json.loads(_edit.extract),
             'validate': json.loads(_edit.validate)}
    return jsonify({'data': _data, 'status': 1})


@api.route('/apiMsg/run', methods=['POST'])
@login_required
def run_api_msg():
    """ 跑接口信息 """
    data = request.json
    project_id = data.get('projectId')
    config_id = data.get('configId')
    api_msg_data = parameter_validator(data.get('apiMsgData'), msg='请勾选信息后，再进行测试', status=0)

    # 前端传入的数据不是按照编号来的，所以这里重新排序
    api_ids = [(item['num'], item['apiMsgId']) for item in api_msg_data]
    api_ids.sort(key=lambda x: x[0])
    # api_data = [ApiMsg.query.filter_by(id=c[1]).first() for c in api_ids]
    api_ids = [c[1] for c in api_ids]

    d = RunCase(project_id)
    d.get_api_test(api_ids, config_id)
    res = json.loads(d.run_case())
    return jsonify({'msg': '测试完成', 'data': res, 'status': 1})


@api.route('/apiMsg/find', methods=['POST'])
@login_required
def find_api_msg():
    """ 查接口信息 """
    data = request.json
    api_name = data.get('apiName') if data.get('apiName') else ""
    api_address = data.get('apiAddress') if data.get('apiAddress') else ""
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 20
    # project_id = parameter_validator(data.get('projectId'), msg='请选择项目', status=0)
    api_set_id = parameter_validator(data.get('apiSetId'), msg='请先在当前项目下选择集合', status=0)

    if api_name or api_address:
        _data = ApiMsg.query.filter_by(api_set_id=api_set_id).filter(and_(ApiMsg.name.like('%{}%'.format(api_name)),
                                                                          ApiMsg.url.like('%{}%'.format(api_address))))
        # total = len(api_data)
        if not _data:
            return jsonify({'msg': '没有该接口信息', 'status': 0})
    else:
        _data = ApiMsg.query.filter_by(api_set_id=api_set_id)

    pagination = _data.order_by(ApiMsg.num.asc()).paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [{'num': c.num,
                 'name': c.name,
                 'desc': c.desc,
                 'url': c.url,
                 'skip': c.skip,
                 'apiMsgId': c.id,
                 'method': c.method,
                 'api_set_id': c.api_set_id,
                 'variableType': c.variable_type,
                 'variable': json.loads(c.variable),
                 'json_variable': c.json_variable,
                 'extract': json.loads(c.extract),
                 'validate': json.loads(c.validate),
                 'param': json.loads(c.param),
                 'header': json.loads(c.header),
                 'parameters': '[]',
                 # 'check': False,
                 'statusCase': {'extract': [True, True], 'variable': [True, True],
                                'validate': [True, True], 'param': [True, True],
                                'header': [True, True], 'parameters': False},
                 'status': True, 'case_name': c.name, 'down_func': c.down_func, 'up_func': c.up_func, 'time': 1}
                for c in items]
    return jsonify({'data': end_data, 'total': total, 'status': 1})


@api.route('/apiMsg/del', methods=['POST'])
@login_required
def del_api_msg():
    """ 删除接口信息 """
    data = request.json
    api_msg_id = data.get('apiMsgId')
    _data = ApiMsg.query.filter_by(id=api_msg_id).first()

    project_id = ApiSet.query.filter_by(id=_data.api_set_id).first().project_id
    if current_user.id not in json.loads(Project.query.filter_by(id=project_id).first().principal):
        return jsonify({'msg': '不能删除别人项目下的接口', 'status': 0})

    # 同步删除接口信息下对应用例下的接口步骤信息
    for d in CaseData.query.filter_by(api_msg_id=api_msg_id).all():
        db.session.delete(d)

    db.session.delete(_data)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/apiMsg/fileChange', methods=['POST'])
@login_required
def file_change():
    """ 导入接口信息 """
    data = request.json
    project_id = parameter_validator(data.get('projectId'), msg='请先选择项目', status=0)
    api_set_id = parameter_validator(data.get('apiSetId'), msg='请先选择集合', status=0)
    import_api_address = parameter_validator(data.get('importApiAddress'), msg='请上传文件', status=0)
    api_list = swagger_change(import_api_address)
    # print(api_list)
    case_num = auto_num(None, ApiMsg, api_set_id=api_set_id)
    for num, api_msg in enumerate(api_list):
        # if '/api/v1.0/weaver/submitRequest' in api_msg['url']:
        api_msg.update({k: json.dumps(v, ensure_ascii=False) for k, v in api_msg.items() if
                        isinstance(v, dict) or isinstance(v, list)})
        print(api_msg['name'])
        _data = ApiMsg.query.filter_by(api_set_id=api_set_id).filter(
            and_(ApiMsg.url.like('%{}%'.format(api_msg['url'])), ApiMsg.method == api_msg['method'])).first()
        # print(_data)
        print(_data)
        # print(api_msg['url'])
        if not _data:
            new_case = ApiMsg(project_id=project_id, api_set_id=api_set_id, num=case_num + num, **api_msg)
            db.session.add(new_case)
            db.session.commit()
        # break
    return jsonify({'msg': '导入成功', 'status': 1})
