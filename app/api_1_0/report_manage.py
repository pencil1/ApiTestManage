import json
import copy
from urllib import parse
from flask import jsonify, request
from . import api, login_required
from app.models import *
from ..util.http_run import RunCase
from ..util.global_variable import *
from ..util.report.report import render_html_report
# from flask_login import current_user
from ..util.validators import parameter_validator


@api.route('/report/run', methods=['POST'])
@login_required
def run_cases():
    """ 跑接口 """
    data = request.json
    project_id = parameter_validator(data.get('projectId'), msg='请先选择项目', status=0)
    case_ids = parameter_validator(data.get('caseIds'), msg='请选择用例', status=0)

    d = RunCase(project_id)
    d.get_case_test(case_ids)
    jump_res = d.run_case()
    if data.get('reportStatus'):
        d.build_report(jump_res, case_ids, parse.unquote(request.headers.get('name')))
    res = json.loads(jump_res)

    return jsonify({'msg': '测试完成', 'status': 1, 'data': {'report_id': d.new_report_id, 'data': res}})


@api.route('/report/list', methods=['POST'])
def get_report():
    """ 查看报告 """
    data = request.json
    report_id = data.get('reportId')
    state = data.get('state')
    _address = REPORT_ADDRESS + str(report_id) + '.txt'

    if not os.path.exists(_address):
        report_data = Report.query.filter_by(id=report_id).first()
        report_data.read_status = '异常'
        db.session.commit()
        return jsonify({'msg': '报告还未生成、或生成失败', 'status': 0})

    report_data = Report.query.filter_by(id=report_id).first()
    report_data.read_status = '已读'
    db.session.commit()
    with open(_address, 'r') as f:
        d = json.loads(f.read())

    if state == 'success':
        _d = copy.deepcopy(d['details'])
        d['details'].clear()
        for d1 in _d:
            if d1['success']:
                d['details'].append(d1)
    elif state == 'error':
        _d = copy.deepcopy(d['details'])
        d['details'].clear()
        for d1 in _d:
            if not d1['success']:
                d['details'].append(d1)
    return jsonify(d)


@api.route('/report/download', methods=['POST'])
@login_required
def download_report():
    """ 报告下载 """
    data = request.json
    report_id = data.get('reportId')
    _address = REPORT_ADDRESS + str(report_id) + '.txt'
    with open(_address, 'r') as f:
        res = json.loads(f.read())
    d = render_html_report(res)
    return jsonify({'data': d, 'status': 1})


@api.route('/report/del', methods=['POST'])
@login_required
def del_report():
    """ 删除报告 """
    data = request.json
    report_id = data.get('report_id')
    _edit = Report.query.filter_by(id=report_id).first()
    db.session.delete(_edit)
    db.session.commit()
    address = str(report_id) + '.txt'
    if not os.path.exists(REPORT_ADDRESS + address):
        return jsonify({'msg': '删除成功', 'status': 1})
    else:
        os.remove(REPORT_ADDRESS + address)
        return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/report/find', methods=['POST'])
@login_required
def find_report():
    """ 查找报告 """
    data = request.json
    project_id = data.get('projectId')
    case_name = data.get('caseName')
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10
    if case_name:
        _data = Report.query.filter_by(project_id=project_id).filter(Report.case_names.like('%{}%'.format(case_name)))
        if not _data:
            return jsonify({'msg': '没有该用例报告', 'status': 0})
    else:
        _data = Report.query.filter_by(project_id=project_id)
    pagination = _data.order_by(Report.create_time.desc()).paginate(page, per_page=per_page, error_out=False)
    items = pagination.items
    total = pagination.total
    end_data = [
        {'name': c.case_names, 'project_id': project_id, 'id': c.id, 'read_status': c.read_status, 'result': c.result,
         'performer': c.performer, 'project_name': Project.query.filter_by(id=project_id).first().name,
         'create_time': str(c.create_time).split('.')[0]} for c in items]

    return jsonify({'data': end_data, 'total': total, 'status': 1})

# END
