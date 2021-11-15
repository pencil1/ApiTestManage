import time

from flask import jsonify, request
from . import api
from app.models import *
import json
from ..util.custom_decorator import login_required
from flask_login import current_user
from sqlalchemy import text


@api.route('/proGather/list')
@login_required
def get_pro_gather():
    """ 获取基本信息 """
    # data = request.query_string
    # print(dir(request))
    # print(data)
    # if current_user.id == 4:
    # _pros = P"""
    #     select project.id, config.id as config_id, config.name as config_name from project
    #     left join config
    #     on project.id = config.project_id
    #     """roject.query.order_by(case((Project.user_id == current_user.id, 1))).all()
    _d = []
    sql = """
        SELECT * FROM `project`
        ORDER BY CASE when user_id={} then 0 end DESC, id DESC
        """.format(current_user.id)
    project_data = list(db.session.execute(sql))
    sql = """
    select project.id, config.id as config_id, config.name as config_name from project 
    left join config
    on project.id = config.project_id
    """
    config_d = list(db.session.execute(sql))

    sql = """
        select project.id, module.id as module_id, module.name as module_name from project 
        left join module
        on project.id = module.project_id
        """
    module_d = list(db.session.execute(sql))

    sql = """
        select project.id, case_set.id as case_set_id, case_set.name as case_set_name from project 
        left join case_set
        on project.id = case_set.project_id
        """
    case_set_d = list(db.session.execute(sql))
    user_pros = False

    for p in project_data:
        if p[0] == current_user.id:
            user_pros = True
        # print(p.id)
        # 获取每个项目下的url
        if p[6] == 'first':
            url = json.loads(p[2])
        elif p[6] == 'second':
            url = json.loads(p[3])
        elif p[6] == 'third':
            url = json.loads(p[4])
        else:
            url = json.loads(p[5])

        _d.append({'name': p.name,
                   'id': p.id,
                   'url': url,
                   'config_data': [{'id': d[1], 'name': d[2]} for d in config_d if d[0] == p[0] and d[1]],
                   'module_data': [{'id': d[1], 'name': d[2]} for d in module_d if d[0] == p[0] and d[1]],
                   'set_data': [{'id': d[1], 'name': d[2]} for d in case_set_d if d[0] == p[0] and d[1]], })
    # s = time.time()
    #
    # my_pros = Project.query.filter_by(user_id=current_user.id).first()
    # e1 = time.time()
    # print(e1-s)

    # for p in _pros:
    #     # pro_and_id[p.name] = p.id
    #
    #     pro_and_id.append({'name': p.name, 'id': p.id})
    #
    #     if b'case' in request.query_string:
    #         # 获取每个项目下的配置信息
    #         scene_config_lists[p.id] = [{'name': c.name, 'configId': c.id} for c in p.configs]
    #
    #         # 获取每个项目下的接口模块
    #         pro[p.id] = [{'name': m.name, 'moduleId': m.id} for m in p.modules]
    #     #
    #     if b'task' in request.query_string:
    #         # 获取每个项目下的用例集
    #         set_list[p.id] = [{'label': s.name, 'id': s.id} for s in p.case_sets]
    #
    #         # 获取每个用例集的用例
    #         for s in p.case_sets:
    #             scene_list["{}".format(s.id)] = [{'label': case.name, 'id': case.id} for case in
    #                                              s.cases]
    #             # scene_list["{}".format(s.id)] = [{'label': scene.name, 'id': scene.id} for scene in
    #             #                                  Case.get_all(case_set_id=s.id)]
    #
    #     # 获取每个项目下的url
    #     if p.environment_choice == 'first':
    #         pro_url[p.id] = json.loads(p.host)
    #     elif p.environment_choice == 'second':
    #         pro_url[p.id] = json.loads(p.host_two)
    #     elif p.environment_choice == 'third':
    #         pro_url[p.id] = json.loads(p.host_three)
    #     elif p.environment_choice == 'fourth':
    #         pro_url[p.id] = json.loads(p.host_four)
    #
    # if my_pros:
    #     # my_pros = {'pro_name': my_pros.name, 'pro_id': my_pros.id, 'model_list': pro[my_pros.name]}
    #     user_pros = True
    # return jsonify(
    #     {'data': True, 'user_pros': True, })
    return jsonify(
        {'data': _d, 'user_pros': user_pros, })


# return jsonify(
#     {'data': pro, 'urlData': pro_url, 'status': 1, 'config_name_list': scene_config_lists,
#      'user_pros': user_pros,
#      'set_list': set_list, 'scene_list': scene_list, 'pro_and_id': pro_and_id})


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
        _data = Project.query.order_by(Project.id.asc())
    pagination = _data.paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [{'id': c.id,
                 'host': c.host,
                 'name': c.name,
                 'choice': c.environment_choice,
                 'principal': User.query.filter_by(id=c.user_id).first().name,
                 'host_two': c.host_two, 'host_three': c.host_three, 'host_four': c.host_four} for c in items]
    return jsonify({'data': end_data, 'total': total, 'status': 1, 'userData': user_data})


@api.route('/project/add', methods=['POST'])
@login_required
def add_project():
    """ 项目增加、编辑 """
    data = request.json
    project_name = data.get('projectName')
    if not project_name:
        return jsonify({'msg': '项目名称不能为空', 'status': 0})
    user_id = data.get('userId')
    if not user_id:
        return jsonify({'msg': '请选择负责人', 'status': 0})
    # principal = data.get('principal')
    environment_choice = data.get('environmentChoice')
    host = json.dumps(data.get('host'))
    host_two = json.dumps(data.get('hostTwo'))
    host_three = json.dumps(data.get('hostThree'))
    host_four = json.dumps(data.get('hostFour'))
    ids = data.get('id')
    header = data.get('header')
    variable = data.get('variable')
    func_file = json.dumps(data.get('funcFile')) if data.get('funcFile') else json.dumps([])
    # func_file='123'
    # print(func_file)
    if ids:
        old_project_data = Project.get_first(id=ids)
        if Project.get_first(name=project_name) and project_name != old_project_data.name:
            return jsonify({'msg': '项目名字重复', 'status': 0})
        else:
            old_project_data.name = project_name
            old_project_data.user_id = user_id
            old_project_data.environment_choice = environment_choice
            old_project_data.host = host
            old_project_data.host_two = host_two
            old_project_data.host_three = host_three
            old_project_data.host_four = host_four
            old_project_data.headers = header
            old_project_data.variables = variable
            old_project_data.func_file = func_file
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Project.get_first(name=project_name):
            return jsonify({'msg': '项目名字重复', 'status': 0})
        else:
            new_project = Project(name=project_name,
                                  host=host,
                                  host_two=host_two,
                                  user_id=user_id,
                                  func_file=func_file,
                                  environment_choice=environment_choice,
                                  host_three=host_three, host_four=host_four, headers=header, variables=variable)
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

    if current_user.id != 1 and current_user.id != pro_data.user_id:
        print(current_user.id)
        return jsonify({'msg': '不能删除别人创建的项目', 'status': 0})
    if pro_data.modules:
        return jsonify({'msg': '请先删除项目下的接口模块', 'status': 0})
    if pro_data.case_sets:
        return jsonify({'msg': '请先删除项目下的业务集', 'status': 0})
    if pro_data.configs:
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
             'principal': _edit.principal,
             'func_file': json.loads(_edit.func_file),
             'host': json.loads(_edit.host),
             'host_two': json.loads(_edit.host_two),
             'host_three': json.loads(_edit.host_three),
             'host_four': json.loads(_edit.host_four),
             'headers': json.loads(_edit.headers),
             'environment_choice': _edit.environment_choice,
             'variables': json.loads(_edit.variables)}
    return jsonify({'data': _data, 'status': 1})
