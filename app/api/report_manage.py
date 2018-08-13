import json
import copy
from flask import jsonify, request
from . import api
from app.models import *
from ..util.http_run import RunCase
from ..util.global_variable import *
from ..util.report import render_html_report


@api.route('/projectGather/list')
def get_project_gather():
    _pros = Project.query.all()
    pro = {}
    for p in _pros:
        modules = Module.query.filter_by(project_id=p.id).all()
        if modules:
            pro[p.name] = [{'value': _gat.name, 'ids': _gat.id} for _gat in modules]
        else:
            pro[p.name] = ['']
    return jsonify(pro)


@api.route('/report/run', methods=['POST'])
def run_cases():
    data = request.json
    if not data.get('projectName') and not data.get('sceneNames'):
        return jsonify({'msg': '请选择项目或模块', 'status': 0})
    run_case = RunCase(data.get('projectName'), data.get('sceneNames'))
    run_case.run_case()
    return jsonify({'msg': '测试完成', 'status': 1, 'data': {'report_id': run_case.new_report_id}})


@api.route('/report/list', methods=['POST'])
def get_report():
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
def download_report():
    data = request.json
    report_id = data.get('reportId')
    _address = REPORT_ADDRESS + str(report_id) + '.txt'
    with open(_address, 'r') as f:
        res = json.loads(f.read())
    d = render_html_report(res, html_report_template=r'{}/report_template.html'.format(TEMP_REPORT))
    # with open(_address, "r", encoding='utf-8') as f:
    #     d = f.read()
    return jsonify({'data': d, 'status': 1})


@api.route('/report/del', methods=['POST'])
def del_report():
    data = request.json
    address = data.get('address') + '.txt'
    _edit = Report.query.filter_by(data=address).first()
    db.session.delete(_edit)
    address = address.split('/')[-1]
    if not os.path.exists(REPORT_ADDRESS + address):
        return jsonify({'msg': '删除成功', 'status': 1})
    else:
        os.remove(REPORT_ADDRESS + address)
        return jsonify({'msg': '删除成功', 'status': 1})


@api.route('/report/find', methods=['POST'])
def find_report():
    data = request.json
    belong_pro = data.get('belong')
    page = data.get('page') if data.get('page') else 1
    per_page = data.get('sizePage') if data.get('sizePage') else 10

    report_data = Report.query.filter_by(belong_pro=belong_pro)
    pagination = report_data.order_by(Report.timestamp.desc()).paginate(page, per_page=per_page, error_out=False)
    report = pagination.items
    total = pagination.total
    report = [{'name': c.name, 'belong': c.belong_pro, 'id': c.id, 'read_status': c.read_status,
               'address': c.data.replace('.txt', '')} for c in report]
    return jsonify({'data': report, 'total': total, 'status': 1})


@api.route('/proScene/list')
def get_pro_scene():
    _pros = Project.query.all()
    pro = {}
    for p in _pros:
        scenes = Scene.query.filter_by(project_id=p.id).all()
        if scenes:
            pro[p.name] = [{'value': _gat.name, 'ids': _gat.id} for _gat in scenes]
        else:
            pro[p.name] = ['']
    return jsonify(pro)

# END
