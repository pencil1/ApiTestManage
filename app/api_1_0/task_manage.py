import json
from flask import jsonify, request
from . import api
from app.models import Task, CaseSet, Case, db, User
from ..util.custom_decorator import login_required
from app import scheduler
from ..util.http_run import RunCase
from ..util.utils import change_cron, auto_num
# from ..util.emails.SendEmail import SendEmail, send_ding_ding_msg
from ..util.report.report import render_html_report
from flask_login import current_user
from ..util.validators import parameter_validator


def aps_test(project_id, case_ids, send_address=None, send_password=None, task_to_address=None, performer='无',
             send_email_status='1', webhook=None, secret=None, title=None):
    # global db
    # db.session.remove()
    # db.create_scoped_session()
    d = RunCase(project_id)
    d.get_case_test(case_ids)
    jump_res = d.run_case()
    d.build_report(jump_res, case_ids, performer)
    res = json.loads(jump_res)

    if send_email_status == '1' or (send_email_status == '2' and not res['success']):

        file = render_html_report(res)
        if task_to_address:
            task_to_address = task_to_address.split(',')
            # SendEmail('yuanzhenwei@aulton.com', 'kPB7hmVVU9FZgGCn', task_to_address, file).send_email()
        if webhook and secret:
            pass
            # msg = f"用例结果：成功{res['stat']['testcases']['success']}条，失败{res['stat']['testcases']['fail']}条"
            # report_address = f'http://test_tools.aulton.com:18080/#/reportShow?reportId={d.new_report_id}'
            # send_ding_ding_msg(report_address, webhook, secret, msg, title)

    db.session.rollback()  # 把连接放回连接池，不知道为什么定时任务跑完不会自动放回去，导致下次跑的时候，mysql连接超时断开报错
    return d.new_report_id


def get_case_id(pro_id, set_id, case_id):
    if len(case_id) != 0:
        return case_id
        # case_ids += [i['id'] for i in case_id]
    else:
        case_ids = []
        if len(case_id) == 0 and len(set_id) != 0:
            _set_ids = set_id
        else:
            _set_ids = [_set.id for _set in
                        CaseSet.query.filter_by(project_id=pro_id).order_by(CaseSet.num.asc()).all()]

        for set_id in _set_ids:
            for case_data in Case.query.filter_by(case_set_id=set_id).order_by(Case.num.asc()).all():
                case_ids.append(case_data.id)
        return case_ids


@api.route('/task/run', methods=['POST'])
@login_required
def run_task():
    """ 单次运行任务 """
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    cases_id = get_case_id(_data.project_id, json.loads(_data.set_id), json.loads(_data.case_id))
    new_report_id = aps_test(_data.project_id, cases_id, _data.task_send_email_address, _data.email_password,
                             _data.task_to_email_address, User.query.filter_by(id=current_user.id).first().name,
                             _data.send_email_status, _data.webhook, _data.secret, _data.title, )

    return jsonify({'msg': '测试成功', 'status': 1, 'data': {'report_id': new_report_id}})


@api.route('/task/start', methods=['POST'])
@login_required
def start_task():
    """ 任务开启 """
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    config_time = change_cron(_data.task_config_time)
    cases_id = get_case_id(_data.project_id, json.loads(_data.set_id), json.loads(_data.case_id))
    scheduler.add_job(func=aps_test, trigger='cron', misfire_grace_time=60, coalesce=False,
                      args=[_data.project_id, cases_id, _data.task_send_email_address, _data.email_password,
                            _data.task_to_email_address, User.query.filter_by(id=current_user.id).first().name,
                            _data.send_email_status, _data.webhook, _data.secret,_data.title,  ],
                      id=str(ids), **config_time)  # 添加任务
    _data.status = '启动'
    db.session.commit()

    return jsonify({'msg': '启动成功', 'status': 1})


@api.route('/task/add', methods=['POST'])
@login_required
def add_task():
    """ 任务添加、修改 """
    data = request.json
    project_id = parameter_validator(data.get('projectId'), msg='请先选择项目', status=0)
    set_ids = data.get('setIds')
    case_ids = data.get('caseIds')
    task_id = data.get('id')
    num = auto_num(data.get('num'), Task, project_id=project_id)
    name = data.get('name')
    task_type = 'cron'
    to_email = data.get('toEmail')
    send_email = data.get('sendEmail')
    webhook = data.get('webhook')
    secret = data.get('secret')
    title = data.get('title')
    password = data.get('password')
    send_email_status = data.get('sendEmailStatus')
    # 0 0 1 * * *
    # if not (not to_email and not send_email and not password) and not (to_email and send_email and password):
    #     return jsonify({'msg': '发件人、收件人、密码3个必须都为空，或者都必须有值', 'status': 0})

    time_config = data.get('timeConfig')
    if len(time_config.strip().split(' ')) != 6:
        return jsonify({'msg': 'cron格式错误', 'status': 0})

    if task_id:
        old_task_data = Task.query.filter_by(id=task_id).first()
        if Task.query.filter_by(task_name=name).first() and name != old_task_data.task_name:
            return jsonify({'msg': '任务名字重复', 'status': 0})
        else:
            old_task_data.project_id = project_id
            old_task_data.set_id = json.dumps(set_ids)
            old_task_data.case_id = json.dumps(case_ids)
            old_task_data.task_name = name
            old_task_data.task_type = task_type
            old_task_data.task_to_email_address = to_email
            old_task_data.task_send_email_address = send_email
            old_task_data.webhook = webhook
            old_task_data.secret = secret
            old_task_data.title = title
            old_task_data.email_password = password
            old_task_data.num = num
            old_task_data.send_email_status = send_email_status
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
            new_task = Task(task_name=name,
                            project_id=project_id,
                            set_id=json.dumps(set_ids),
                            case_id=json.dumps(case_ids),
                            email_password=password,
                            task_type=task_type,
                            task_to_email_address=to_email,
                            task_send_email_address=send_email,
                            webhook=webhook,
                            secret=secret,
                            title=title,
                            task_config_time=time_config,
                            send_email_status=send_email_status,
                            num=num)
            db.session.add(new_task)
            db.session.commit()
            return jsonify({'msg': '新建成功', 'status': 1})


@api.route('/task/edit', methods=['POST'])
@login_required
def edit_task():
    """ 返回待编辑任务信息 """
    data = request.json
    task_id = data.get('id')
    c = Task.query.filter_by(id=task_id).first()
    _data = {'num': c.num,
             'task_name': c.task_name,
             'task_config_time': c.task_config_time,
             'task_type': c.task_type,
             'set_ids': json.loads(c.set_id),
             'case_ids': json.loads(c.case_id),
             'task_to_email_address': c.task_to_email_address,
             'task_send_email_address': c.task_send_email_address,
             'webhook': c.webhook,
             'secret': c.secret,
             'title': c.title,
             'password': c.email_password,
             'send_email_status': c.send_email_status}

    return jsonify({'data': _data, 'status': 1})


@api.route('/task/find', methods=['POST'])
@login_required
def find_task():
    """ 查找任务信息 """
    data = request.json
    project_id = data.get('projectId')
    task_name = data.get('taskName')
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    # CaseSet.get_all(project_id=project_id)
    # set_list = []
    # # 获取每个项目下的用例集
    # set_list[p.id] = [{'label': s.name, 'id': s.id} for s in p.case_sets]
    # scene_list= []
    # # 获取每个用例集的用例
    # for s in p.case_sets:
    #     scene_list["{}".format(s.id)] = [{'label': scene.name, 'id': scene.id} for scene in
    #                                      Case.get_all(case_set_id=s.id)]

    if task_name:
        _data = Task.query.filter_by(project_id=project_id).filter(Task.task_name.like('%{}%'.format(task_name)))
        if not _data:
            return jsonify({'msg': '没有该任务', 'status': 0})
    else:
        _data = Task.query.filter_by(project_id=project_id)
    pagination = _data.order_by(Task.id.asc()).paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [{'task_name': c.task_name, 'task_config_time': c.task_config_time,
                 'id': c.id, 'task_type': c.task_type, 'status': c.status} for c in items]
    return jsonify({'data': end_data, 'total': total, 'status': 1})


@api.route('/task/del', methods=['POST'])
@login_required
def del_task():
    """ 删除任务信息 """
    data = request.json
    ids = data.get('id')
    _edit = Task.query.filter_by(id=ids).first()
    if _edit.status != '创建':
        return jsonify({'msg': '请先移除任务', 'status': 0})

    db.session.delete(_edit)
    db.session.commit()
    return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/task/pause', methods=['POST'])
@login_required
def pause_task():
    """ 暂停任务 """
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
    """ 恢复任务 """
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
    """ 移除任务 """
    data = request.json
    ids = data.get('id')
    _data = Task.query.filter_by(id=ids).first()
    _data.status = '创建'
    db.session.commit()
    try:
        scheduler.remove_job(str(ids))  # 移除任务
    except Exception as e:
        print(e)
    return jsonify({'msg': '移除成功', 'status': 1})
