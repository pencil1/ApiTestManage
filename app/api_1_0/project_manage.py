from flask import jsonify, request
from . import api
from app.models import *
import json
from ..util.custom_decorator import login_required
from ..util.utils import auto_num, num_sort, tree_change
from flask_login import current_user
from ..util.validators import parameter_validator
import os


@api.route('/proGather/list')
@login_required
def get_pro_gather():
    """ 获取基本信息 """
    _d = []
    if os.getenv('FLASK_CONFIG'):
        sql = """
                SELECT * FROM `project` ORDER BY CASE when  principal REGEXP '[^1-9]{}[^1-9]' then 0 end DESC, num ASC
                    """.format(current_user.id)
    else:
        sql = """
                SELECT * FROM `project`
                ORDER BY CASE when  user_id={} then 0 end DESC, num ASC
                """.format(current_user.id)

    project_data = list(db.session.execute(sql))

    sql = """
    select project.id, config.id as config_id, config.name as config_name from project 
    left join config
    on project.id = config.project_id
    """
    config_d = list(db.session.execute(sql))

    sql = """
        select project.id as project_id, api_set.id as api_set_id, api_set.name as api_set_name,api_set.higher_id as api_set_higher_id, api_set.num as api_set_num from api_set 
        left join project
        on project.id = api_set.project_id
        ORDER BY api_set.higher_id
        """
    # api_set_d = list(db.session.execute(sql))
    api_set_d = tree_change(
        [{'project_id': _d[0], 'id': _d[1], 'name': _d[2], 'higher_id': _d[3], 'num': _d[4]} for _d in
         list(db.session.execute(sql))])
    sql = """
        select project.id as project_id, case_set.id as case_set_id, case_set.name as case_set_name,case_set.higher_id as case_set_higher_id, case_set.num as case_set_num from case_set 
        left join project
        on project.id = case_set.project_id
        ORDER BY case_set.higher_id
        """
    case_set_d = tree_change(
        [{'project_id': _d[0], 'id': _d[1], 'name': _d[2], 'higher_id': _d[3], 'num': _d[4]} for _d in
         list(db.session.execute(sql))])
    user_pros = False
    for p in project_data:
        if current_user.id in json.loads(p.principal):
            # print(current_user.id,json.loads(p.principal))
            user_pros = True
        _d.append({'name': p.name,
                   'id': p.id,
                   'url': json.loads(p.environment_list)[int(p.environment_choice)-1]['urls'],
                   'config_data': [{'id': d[1], 'name': d[2]} for d in config_d if d[0] == p[0] and d[1]],
                   'api_set_data': [d for d in api_set_d if p.id == d['project_id']],
                   'case_set_data': [d for d in case_set_d if p.id == d['project_id']],

                   })

    return jsonify(
        {'data': _d, 'user_pros': user_pros, })


@api.route('/project/find', methods=['POST'])
@login_required
def find_project():
    """ 查找项目 """
    data = request.json
    project_name = data.get('projectName')

    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    user_data = [{'user_id': u.id, 'user_name': u.name} for u in User.query.all()]
    if project_name:
        _data = Project.query.filter(Project.name.like('%{}%'.format(project_name)))
        if not _data:
            return jsonify({'msg': '没有该项目', 'status': 0})
    else:
        _data = Project.query.order_by(Project.num.asc())
    pagination = _data.paginate(page, per_page=per_page, error_out=False)
    # pagination = _data.order_by(Project.num.asc()).paginate(page, per_page=per_page, error_out=False)

    items = pagination.items
    total = pagination.total
    end_data = [{'id': c.id,
                 # 'host': c.host,
                 'num': c.num,
                 'name': c.name,
                 'choice': c.environment_choice,
                 'principal': json.loads(c.principal),} for c in items]
    return jsonify({'data': end_data, 'total': total, 'status': 1, 'userData': user_data})


@api.route('/project/add', methods=['POST'])
@login_required
def add_project():
    """ 项目增加、编辑 """
    data = request.json
    project_name = parameter_validator(data.get('projectName'), msg='项目名称不能为空', status=0)
    principal = parameter_validator(json.dumps(data.get('principal')), msg='请选择负责人', status=0)
    user_id = data.get('userId')
    environment_choice = data.get('environmentChoice')
    environment_list = json.dumps(data.get('environmentList'))
    ids = data.get('id')
    header = data.get('header')
    variable = data.get('variable')
    func_file = json.dumps(data.get('funcFile')) if data.get('funcFile') else json.dumps([])
    num = auto_num(data.get('num'), Project)
    if ids:
        old_project_data = Project.get_first(id=ids)
        if Project.get_first(name=project_name) and project_name != old_project_data.name:
            return jsonify({'msg': '项目名字重复', 'status': 0})
        else:
            list_data = Project.query.filter_by(user_id=user_id).all()
            num_sort(num, old_project_data.num, list_data, old_project_data)
            old_project_data.name = project_name
            # old_project_data.user_id = user_id
            old_project_data.environment_choice = environment_choice
            old_project_data.environment_list = environment_list
            old_project_data.num = num
            old_project_data.headers = header
            old_project_data.variables = variable
            old_project_data.func_file = func_file
            old_project_data.principal = principal
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Project.get_first(name=project_name):
            return jsonify({'msg': '项目名字重复', 'status': 0})
        else:
            new_project = Project(name=project_name,
                                  num=num,
                                  user_id=user_id,
                                  principal=principal,
                                  func_file=func_file,
                                  environment_choice=environment_choice,
                                  environment_list=environment_list,
                                  headers=header,
                                  variables=variable)
            db.session.add(new_project)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/project/del', methods=['POST'])
@login_required
def del_project():
    """ 删除项目 """
    data = request.json
    ids = data.get('id')
    pro_data = Project.get_first(id=ids)
    if current_user.id not in json.loads(pro_data.principal):
        return jsonify({'msg': '不能删除别人创建的项目', 'status': 0})
    if pro_data.api_sets.all():
        return jsonify({'msg': '请先删除项目下的接口模块', 'status': 0})
    if pro_data.case_sets.all():
        return jsonify({'msg': '请先删除项目下的业务集', 'status': 0})
    if pro_data.configs.all():
        return jsonify({'msg': '请先删除项目下的业务配置', 'status': 0})
    db.session.delete(pro_data)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/project/edit', methods=['POST'])
@login_required
def edit_project():
    """ 返回待编辑项目信息 """
    data = request.json
    pro_id = data.get('id')
    _edit = Project.get_first(id=pro_id)
    _data = {'pro_name': _edit.name,
             'user_id': _edit.user_id,
             'num': _edit.num,
             'principal': json.loads(_edit.principal),
             'func_file': json.loads(_edit.func_file),
             'headers': json.loads(_edit.headers),
             'environment_choice': _edit.environment_choice,
             'environment_list': json.loads(_edit.environment_list),
             'variables': json.loads(_edit.variables),
             }
    return jsonify({'data': _data, 'status': 1})
