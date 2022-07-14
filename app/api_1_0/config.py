from flask import jsonify, request
from . import api
from app.models import *
from ..util.custom_decorator import login_required
from ..util.utils import *
from flask_login import current_user
from ..util.validators import parameter_validator


@api.route('/config/add', methods=['POST'])
@login_required
def add_scene_config():
    """ 添加配置 """
    data = request.json
    project_id = parameter_validator(data.get('projectId'), msg='请先选择项目', status=0)
    name = parameter_validator(data.get('name'), msg='配置名称不能为空', status=0)
    ids = data.get('id')
    func_address = json.dumps(data.get('funcAddress'))
    variable = data.get('variable')
    if re.search('\${(.*?)}', variable, flags=0) and not func_address:
        return jsonify({'msg': '参数引用函数后，必须引用函数文件', 'status': 0})
    num = auto_num(data.get('num'), Config, project_id=project_id)
    if ids:
        # form = ConfigForm().validate_for_api()
        # print(form.name.data)
        old_data = Config.query.filter_by(id=ids).first()
        old_num = old_data.num
        list_data = Config.query.filter_by(project_id=project_id).all()
        if Config.query.filter_by(name=name, project_id=project_id).first() and name != old_data.name:
            return jsonify({'msg': '配置名字重复', 'status': 0})
        num_sort(num, old_num, list_data, old_data)
        old_data.name = name
        old_data.func_address = func_address
        old_data.project_id = project_id
        old_data.variables = variable
        db.session.commit()
        return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Config.query.filter_by(name=name, project_id=project_id).first():
            return jsonify({'msg': '配置名字重复', 'status': 0})
        else:
            new_config = Config(name=name, variables=variable, project_id=project_id, num=num,
                                func_address=func_address)
            db.session.add(new_config)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/config/find', methods=['POST'])
@login_required
def find_config():
    """ 查找配置 """
    data = request.json
    project_id = data.get('projectId')
    config_name = data.get('configName')
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    if not project_id:
        return jsonify({'msg': '请先创建属于自己的项目', 'status': 0})

    if config_name:
        _data = Config.query.filter_by(project_id=project_id).filter(Config.name.like('%{}%'.format(config_name)))
        if not _data:
            return jsonify({'msg': '没有该配置', 'status': 0})
    else:
        _data = Config.query.filter_by(project_id=project_id)
    pagination = _data.order_by(Config.num.asc()).paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [{'name': c.name, 'id': c.id, 'num': c.num, 'func_address': c.func_address} for c in items]
    return jsonify({'data': end_data, 'total': total, 'status': 1})


@api.route('/config/del', methods=['POST'])
@login_required
def del_config():
    """ 删除配置 """
    data = request.json
    ids = data.get('id')
    _edit = Config.query.filter_by(id=ids).first()
    if current_user.id != Project.query.filter_by(id=_edit.project_id).first().user_id:
        return jsonify({'msg': '不能删除别人项目下的配置', 'status': 0})
    db.session.delete(_edit)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/config/edit', methods=['POST'])
@login_required
def edit_config():
    """ 返回待编辑配置信息 """
    data = request.json
    ids = data.get('id')
    _edit = Config.query.filter_by(id=ids).first()
    _data = {'name': _edit.name,
             'num': _edit.num,
             'variables': json.loads(_edit.variables),
             'func_address': json.loads(_edit.func_address)}
    return jsonify({'data': _data, 'status': 1})
