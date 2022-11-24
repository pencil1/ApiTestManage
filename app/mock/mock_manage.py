from . import mock
from flask import jsonify, request
from app.models import MockApi, db
from sqlalchemy import and_
from ..util.validators import parameter_validator
from app.util.my_importer import install_meta
import json
from ..util.httprunner.parser import parse_string_functions


@mock.route('/mockApi/add', methods=['POST'])
def add_mock_api():
    """
    新增、编辑mock接口
    """
    data = request.json
    ids = data.get('id')
    name = parameter_validator(data.get('name'), msg='mock接口名称不能为空', status=0)
    url = parameter_validator(data.get('url'), msg='mock接口地址不能为空', status=0)
    param_body = data.get('paramBody')
    func = data.get('func')
    method = data.get('method')
    project_id = data.get('projectId')

    if ids:
        old_data = MockApi.get_first(id=ids)
        if MockApi.get_first(url=url) and url != old_data.url:
            return jsonify({'msg': '地址重复', 'status': 0})
        else:
            old_data.name = name
            old_data.url = url
            old_data.param_body = json.dumps(param_body)
            old_data.func = func
            old_data.method = method
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if MockApi.get_first(url=url):
            return jsonify({'msg': 'mock接口地址重复', 'status': 0})
        else:
            new_mock = MockApi(name=name,
                               url=url,
                               param_body=json.dumps(param_body),
                               func=func,
                               project_id=project_id,
                               method=method,
                               )
            db.session.add(new_mock)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1, 'id': new_mock.id})


@mock.route('/mockApi/edit', methods=['POST'])
def edit_mock_api():
    """
    对应id的mock接口数据
    """
    data = request.json
    mock_id = data.get('mockId')
    _edit = MockApi.query.filter_by(id=mock_id).first()
    _data = {'name': _edit.name,
             'method': _edit.method,
             'id': _edit.id,
             'param_body': json.loads(_edit.param_body),
             'url': _edit.url,
             'project_id': _edit.project_id,
             'func': _edit.func,
             }
    return jsonify({'data': _data, 'status': 1})


@mock.route('/mockApi/del', methods=['POST'])
def del_mock_api():
    """
    删除mock接口
    """
    data = request.json
    ids = data.get('id')
    del_data = MockApi.get_first(id=ids)
    db.session.delete(del_data)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@mock.route('/mockApi/find', methods=['POST'])
def find_mock_api():
    """ 查找mock接口 """
    data = request.json
    project_id = data.get('projectId')
    mock_name = data.get('mockName') if data.get('mockName') else ""
    url = data.get('url') if data.get('url') else ""
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    if mock_name or url:
        _data = MockApi.query.filter_by(project_id=project_id).filter(and_(MockApi.name.like('%{}%'.format(mock_name)),
                                                                           MockApi.url.like('%{}%'.format(url))))
        # total = len(api_data)
        if not _data:
            return jsonify({'msg': '没有该接口信息', 'status': 0})
    else:
        _data = MockApi.query.filter_by(project_id=project_id)
    pagination = _data.order_by(MockApi.created_time.desc()).paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [
        {'name': c.name, 'id': c.id, 'url': c.url,
         'create_time': str(c.created_time).split('.')[0]} for c in items]
    return jsonify({'data': end_data, 'total': total, 'status': 1})


@mock.route('/<path:path>', methods=['GET', 'PUT', 'DELETE', 'POST'])
def dispatch_request(path):
    """
    mock view logic
    :param path: request url for mock server
    :return: response msg that use default or custom defined
    """
    # print(request.method)
    # print(path)
    _data = MockApi.query.filter_by(url='/' + path, method=request.method).first()

    for param_body in json.loads(_data.param_body):
        if json.loads(param_body['param']) == request.json:
            if _data.func:
                # print(_data.func)
                body = json.loads(param_body['body'])
                func_list = install_meta(_data.func)
                if 'set_up' in func_list.keys():
                    body = func_list['set_up'](body)
                body = json.loads(parse_string_functions(json.dumps(body), {}, functions_mapping=func_list))
                if 'set_down' in func_list.keys():
                    body = func_list['set_down'](body)
            else:
                body = json.loads(param_body['body'])
            return jsonify(body)
    # print(_data.param_body)
    # body = json.loads(m.body)
    return jsonify({'status': 0, 'msg': '参数有误，找不到匹配的返回数据'})
