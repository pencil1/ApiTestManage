from flask import jsonify, request
from flask_login import current_user
from app.models import *
from . import api
from ..util.http_run import RunCase
from ..util.utils import *


@api.route('/suite/add', methods=['POST'])
def add_suite():
    data = request.json
    ids = data.get('suiteId')
    gather_name = data.get('gatherName')
    suite_name = data.get('suiteName')
    project_name = data.get('projectName')
    project_id = Project.query.filter_by(name=project_name).first().id
    api_data = data.get('apiData')
    if not api_data:
        return jsonify({'msg': '请至少选择1条接口信息', 'status': 1})

    module_id = Module.query.filter_by(name=gather_name, project_id=project_id).first().id
    num = auto_num(data.get('num'), ApiSuite, module_id=module_id)

    if ids:
        old_suite_data = ApiSuite.query.filter_by(id=ids).first()
        old_num = old_suite_data.num
        if ApiSuite.query.filter_by(name=suite_name, module_id=module_id).first() and suite_name != old_suite_data.name:
            return jsonify({'msg': '套件名字重复', 'status': 0})

        elif ApiSuite.query.filter_by(num=num, module_id=module_id).first() and num != old_suite_data.num:

            num_sort(num, old_num, ApiSuite, module_id=module_id)
        else:
            old_suite_data.num = num
        old_suite_data.name = suite_name
        old_suite_data.api_ids = json.dumps(api_data)
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if ApiSuite.query.filter_by(name=suite_name, module_id=module_id).first():
            return jsonify({'msg': '套件名字重复', 'status': 0})
        else:
            new_suite = ApiSuite(name=suite_name, num=num, api_ids=json.dumps(api_data), module_id=module_id)
            db.session.add(new_suite)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/suite/find', methods=['POST'])
def find_suite():
    data = request.json
    model_name = data.get('modelName')
    suite_name = data.get('suiteName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    project_name = data.get('projectName')
    project_id = Project.query.filter_by(name=project_name).first().id
    module_id = Module.query.filter_by(name=model_name, project_id=project_id).first().id

    if suite_name:
        suite = ApiSuite.query.filter_by(module_id=module_id).filter(
            ApiSuite.name.like('%{}%'.format(suite_name))).all()
        if not suite:
            return jsonify({'msg': '没有该套件', 'status': 0})
    else:
        suite = ApiSuite.query.filter_by(module_id=module_id)
        pagination = suite.order_by(ApiSuite.num.asc()).paginate(page, per_page=per_page, error_out=False)
        suite = pagination.items
        total = pagination.total
    suite = [{'name': c.name, 'id': c.id, 'num': c.num,
              'api_names': ', '.join([ApiMsg.query.filter_by(id=i).first().name for i in json.loads(c.api_ids)])}
             for c in suite]

    return jsonify({'data': suite, 'total': total, 'status': 1})


@api.route('/suite/del', methods=['POST'])
def del_suite():
    data = request.json
    suite_id = data.get('suiteId')
    _edit = ApiSuite.query.filter_by(id=suite_id).first()

    project_id = Module.query.filter_by(id=_edit.module_id).first().project_id
    if current_user.id != Project.query.filter_by(id=project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的套件', 'status': 0})
    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/suite/edit', methods=['POST'])
def edit_suite():
    data = request.json
    suite_id = data.get('suiteId')
    _edit = ApiSuite.query.filter_by(id=suite_id).first()
    api_data = [ApiMsg.query.filter_by(id=api_id).first() for api_id in json.loads(_edit.api_ids)]
    _data = {'id': _edit.id, 'name': _edit.name, 'num': _edit.num,
             'apiData': [{'caseId': c.id, 'name': c.name, 'url': c.url} for c in api_data]}

    return jsonify({'data': _data, 'status': 1})


@api.route('/suite/findApi', methods=['POST'])
def find_api():
    data = request.json
    suite_ids = data.get('suiteIds')
    apiData = []
    for suite_id in suite_ids:
        for api_id in json.loads(ApiSuite.query.filter_by(id=suite_id).first().api_ids):
            c = ApiMsg.query.filter_by(id=api_id).first()
            if c.variable_type == 'json':
                variable = c.variables
            else:
                variable = json.loads(c.variables)
            apiData.append(
                {'num': c.num, 'name': c.name, 'desc': c.desc, 'url': c.url, 'caseId': c.id, 'gather_id': c.module_id,
                 'variableType': c.variable_type,
                 'variables': variable, 'extract': json.loads(c.extract),
                 'validate': json.loads(c.validate),
                 'param': json.loads(c.param),
                 'statusCase': {'extract': [True, True], 'variable': [True, True], 'validate': [True, True],
                                'param': [True, True]},
                 'status': True, 'case_name': c.name, 'down_func': '', 'up_func': '', 'time': 1})

    return jsonify({'data': apiData, 'status': 1})
