import os
import json
from flask import jsonify, request
from . import api
from app.models import *
from ..util.login_require import login_required
from app import scheduler
from ..util.http_run import RunCase


def aps_test(project_name, scene_names, trigger=None, task_id=None):
    d = RunCase(project_names=project_name, scene_names=scene_names)
    d.all_cases_data()
    d.run_case()
    if trigger:
        _data = Task.query.filter_by(id=task_id).first()
        _data.status = '创建'
        db.session.commit()


def change_cron(expression):
    args = {}
    expression = expression.split(' ')
    if expression[0] != '0' and expression[0] != '*':
        args['second'] = expression[0]
    if expression[1] != '0' and expression[1] != '*':
        args['minute'] = expression[1]
    if expression[2] != '0' and expression[2] != '*':
        args['hour'] = expression[2]
    if expression[3] != '0' and expression[3] != '*':
        args['day'] = expression[3]
    if expression[4] != '0' and expression[4] != '*':
        args['month'] = expression[4]
    if expression[5] != '0' and expression[5] != '*':
        args['day_of_week'] = expression[5]
    return args


@api.route('/task/start', methods=['POST'])
@login_required
def start_task():
    import datetime
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    _data.status = '启动'
    config_time = change_cron(_data.task_config_time)
    # scheduler.add_job(str(ids), aps_test, trigger='cron', args=['asd'], **config_time)
    if _data.task_type == 'cron':
        scheduler.add_job(aps_test, 'cron', args=[_data.project_name, json.loads(_data.scene_names)], id=str(ids),
                          **config_time)  # 添加任务
    else:
        scheduler.add_job(aps_test, 'date', args=[_data.project_name, json.loads(_data.scene_names), 'date', ids],
                          id=str(ids), run_date=datetime.datetime(*[int(t) for t in _data.task_config_time.split(',')]))
    db.session.commit()

    return jsonify({'msg': '启动成功', 'status': 1})


@api.route('/task/add', methods=['POST'])
def add_task():
    data = request.json
    project_name = data.get('projectName')
    scene_names = data.get('sceneNames')
    task_id = data.get('id')
    num = data.get('num')
    name = data.get('name')
    task_type = data.get('taskType')
    to_email = data.get('toEmail')
    send_email = data.get('sendEmail')
    time_config = data.get('timeConfig')
    if task_type == 'date':
        try:
            datetime.datetime(*[int(t) for t in time_config.split(',')])
            print(datetime.datetime(*[int(t) for t in time_config.split(',')]))
        except Exception as e:
            print(e)
            return jsonify({'msg': '时间配置格式错误', 'status': 0})
    else:
        if len(time_config.strip().split(' ')) != 6:
            return jsonify({'msg': 'cron格式错误', 'status': 0})

    if task_id:
        old_task_data = Task.query.filter_by(id=task_id).first()
        if Task.query.filter_by(task_name=name).first() and name != old_task_data.task_name:
            return jsonify({'msg': '任务名字重复', 'status': 0})
        else:
            old_task_data.project_name = project_name
            old_task_data.scene_names = json.dumps(scene_names)
            old_task_data.task_name = name
            old_task_data.task_type = task_type
            old_task_data.task_to_email_address = to_email
            old_task_data.task_send_email_address = send_email
            old_task_data.num = num
            if old_task_data.status != '创建' and old_task_data.task_config_time != time_config:
                scheduler.reschedule_job(str(task_id), trigger='cron', **change_cron(time_config))  # 修改任务
                old_task_data.status = '启动'

            old_task_data.task_config_time = time_config
            db.session.commit()
            return jsonify({'msg': '修改成功', 'status': 1})
    else:
        if Task.query.filter_by(task_name=name).first():
            return jsonify({'msg': '任务名字重复', 'status': 0})
        else:
            new_task = Task(task_name=name, project_name=project_name, scene_names=json.dumps(scene_names),
                            task_type=task_type, task_to_email_address=to_email, task_send_email_address=send_email,
                            task_config_time=time_config, num=num)
            db.session.add(new_task)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/task/find', methods=['POST'])
def find_task():
    data = request.json
    task_name = data.get('taskName')
    total = 1
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    if task_name:
        _data = Task.query.filter(Task.task_name.like('%{}%'.format(task_name))).all()
        if not _data:
            return jsonify({'msg': '没有该任务', 'status': 0})
    else:
        pagination = Task.query.order_by(Task.id.asc()).paginate(page, per_page=per_page, error_out=False)
        _data = pagination.items
        total = pagination.total

    task = [{'num': c.num, 'task_name': c.task_name, 'task_config_time': c.task_config_time,
             'id': c.id, 'task_type': c.task_type, 'status': c.status} for c in _data]
    return jsonify({'data': task, 'total': total, 'status': 1})


@api.route('/task/edit', methods=['POST'])
def edit_task():
    data = request.json
    task_id = data.get('id')
    c = Task.query.filter_by(id=task_id).first()
    _data = {'num': c.num, 'task_name': c.task_name, 'task_config_time': c.task_config_time,
             'project_name': c.project_name, 'scene_names': json.loads(c.scene_names), 'task_type': c.task_type,
             'task_to_email_address': c.task_to_email_address, 'task_send_email_address': c.task_send_email_address}

    return jsonify({'data': _data, 'status': 1})


@api.route('/task/del', methods=['POST'])
@login_required
def del_task():
    data = request.json
    ids = data.get('id')
    _edit = Task.query.filter_by(id=ids).first()
    if _edit.status != '创建':
        return jsonify({'msg': '请先移除任务', 'status': 0})

    db.session.delete(_edit)
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/task/pause', methods=['POST'])
@login_required
def pause_task():
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    _data.status = '暂停'
    scheduler.pause_job(str(ids))  # 添加任务
    db.session.commit()

    return jsonify({'msg': '暂停成功', 'status': 1})


@api.route('/task/resume', methods=['POST'])
@login_required
def resume_task():
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    _data.status = '启动'
    scheduler.resume_job(str(ids))  # 添加任务
    db.session.commit()
    return jsonify({'msg': '恢复成功', 'status': 1})


@api.route('/task/remove', methods=['POST'])
@login_required
def remove_task():
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    scheduler.remove_job(str(ids))  # 添加任务
    _data.status = '创建'
    db.session.commit()
    return jsonify({'msg': '移除成功', 'status': 1})
