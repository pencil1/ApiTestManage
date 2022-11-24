import glob
import importlib
import os
import types
import random
import requests
from flask import jsonify, request, send_from_directory
from app.models import *
from . import api
from ..util.tool_func import *


# from func_list.asdf import r_data


@api.route('/buildIdentity')
def build_identity():
    c = CaseData.query.all()
    # a = [302, 303, 305, 306, 309, 310, 312, 315, 317, 320, 321, 322, 324, 325, 327, 328, 330, 331, 333, 334, 336, 354, 356, 357, 359, 360, 362, 363, 365, 366, 368, 369, 371, 439]
    # for a1 in a:
    #     a2 = CaseData.query.filter_by(id=a1).first()
    #     print(a1)
    #     print(a2.variable)
    for c1 in c:

        if 'u64cdu4f5cu6210u529f' in c1.validate:
            c1.validate = c1.validate.replace('u64cdu4f5cu6210u529f', '操作成功')

    db.session.commit()
    return jsonify({'msg': '修改完成', 'status': 1})
    # identity_data = ''.join([b + '\n' for b in list(set([identity_generator() for j in range(100)]))])
    # return jsonify({'data': identity_data, 'status': 1})


@api.route('/delSql', methods=['POST'])
def del_sql():
    # for p in _pros:
    #     p.environment_choice = 'first'
    # p.host_two = json.dumps([])
    # p.host_three = json.dumps([])
    # p.host_four = json.dumps([])
    # pro_url = []
    # if p.host:
    #     pro_url.append(p.host)
    # if p.host_two:
    #     pro_url.append(p.host_two)
    # if p.host_three:
    #     pro_url.append(p.host_three)
    # if p.host_four:
    #     pro_url.append(p.host_four)
    # p.host = json.dumps(pro_url)
    a = Config.query.all()
    for a1 in a:
        if a1.func_address:
            if isinstance(json.loads(a1.func_address), list):
                a1.func_address = ','.join(json.loads(a1.func_address))
        else:
            a1.func_address = json.dumps([])

    b = Case.query.all()
    for b1 in b:
        if b1.func_address:
            if isinstance(json.loads(b1.func_address), list):
                b1.func_address = ','.join(json.loads(b1.func_address))
        else:
            b1.func_address = json.dumps([])
    db.session.commit()

    return jsonify({'msg': '修改完成', 'status': 1})


def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)


@api.route('/runCmd', methods=['POST'])
def run_cmd():
    import importlib

    data = request.json
    name = data.get('funcName')
    import_path = 'func_list.build_in_func'
    func_list = importlib.reload(importlib.import_module(import_path))
    module_functions_dict = dict(filter(is_function, vars(func_list).items()))
    module_functions_dict[name]()

    return jsonify({'msg': '完成', 'status': 1})
    # identity_data = [{'identity': b} for b in list(set([identity_generator() for j in range(100)]))]
    # return jsonify({'data': identity_data, 'status': 1, 'title': ['身份证']})


@api.route('/optimizeError', methods=['POST'])
def optimize_error_data():
    data = request.json
    error_data = data.get('errorData')
    new_data = '\n'.join(error_data.split('↵'))
    # data = request.json
    # _data = data.get('dictData')
    # test = json.loads(_data)
    # d = TraverseDict()
    # d.get_dict_keys_path(test)
    # d.data_tidy(test)
    # d.get_dict_keys_path(test)
    # d.data_tidy(test)
    return jsonify({'status': 1, 'msg': '优化成功', 'data': new_data})


@api.route('/optimizeErrorData', methods=['POST'])
def deal_data():
    data1 = CaseData.query.all()
    for d in data1:
        d.time = 1
        db.session.commit()
    # data = request.json
    # _data = data.get('dictData')
    # test = json.loads(_data)
    # d = TraverseDict()
    # d.get_dict_keys_path(test)
    # d.data_tidy(test)
    # d.get_dict_keys_path(test)
    # d.data_tidy(test)
    return jsonify({'status': 1, 'msg': '优化成功'})


@api.route("/downloadFile/<filepath>", methods=['GET'])
def download_file(filepath):
    if filepath == 'newFile':
        list_of_files = glob.glob(r'D:\temp_files\*')  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime).split('\\')[-1]
        return send_from_directory(r'D:\temp_files', latest_file, as_attachment=True)
    else:
        return send_from_directory(r'D:\temp_files', filepath, as_attachment=True)


# 上传文件
@api.route('/upload1', methods=['POST'], strict_slashes=False)
def api_upload1():
    """ 文件上传 """
    data = request.files
    # try:
    file = data['file']
    skip = request.form.get('skip')
    # print(request.form)
    from PIL import Image
    a = Image.open(file)
    a.show()
    return jsonify({"msg": "上传成功", "status": 1})


@api.route('/caseChange', methods=['POST'])
def case_change():
    from func_list.xmindtest import mindtoExcel, mindto_csv
    data = request.json
    address = data.get('address')
    choice = data.get('choice')
    print(type(choice))
    if not address:
        return jsonify({'status': 0, 'msg': '请上传文件'})
    elif choice == 1:
        result_address = mindtoExcel(address).replace('/home', '')
    else:
        result_address = mindto_csv(address).replace('/home', '')

    return jsonify({'status': 1, 'msg': '优化成功', 'data': result_address})


@api.route('/listG', methods=['POST'])
def list_g():
    data = request.json
    # print(request.json)
    code = data.get('list')
    code2 = ','.join([c.split('.')[1].lower() + c.split('.')[0] for c in code])
    header = {'Referer': 'https://finance.sina.com.cn/'}
    result1 = requests.get('https://hq.sinajs.cn/rn=1644460788303&list={}'.format(code2), headers=header)
    _d = result1.text.split(';')[:-1]
    temp = []
    for n, g in enumerate(_d):
        r = g.split(',')
        temp.append("%+.2f" % (round((float(r[3]) - float(r[2])) / float(r[2]) * 100, 2)))
    return jsonify({'status': 1, 'msg': '成功', 'data': temp})


@api.route('/show1', methods=['POST'])
def show1():
    a = Role.query.filter_by(id=1).first()
    a.id = 3
    db.session.commit()

    b = Role.query.filter_by(id=2).first()
    b.id = 1
    db.session.commit()

    b = Role.query.filter_by(id=3).first()
    b.id = 2
    db.session.commit()

    # print(type(student.configs.order_by(Config.num.asc())))
    return jsonify({'status': 1, 'msg': '优化成功', 'data': '1'})


@api.route('/test_json', methods=['get'])
def test_json():
    func_list = importlib.reload(importlib.import_module('func_list.{}'.format('asdf')))
    module_functions_dict = {name: item for name, item in vars(func_list).items()
                             if isinstance(item, types.FunctionType)}
    # print(module_functions_dict['r_data']())
    data = module_functions_dict['r_data']()
    # print(type(student.configs.order_by(Config.num.asc())))
    return jsonify(data)


@api.route('/issues', methods=['get'])
def issues_data():
    issues_id = request.args.get("issues_id")
    headers1 = {'PRIVATE-TOKEN': '1EwTWvwzzDyUm3UzNrVu'}
    # r1 = requests.get('http://120.76.207.186/api/v4/projects', headers=headers1)

    r1 = requests.get('http://120.76.207.186/api/v4/projects/848/issues?iids[]={}'.format(issues_id), headers=headers1)
    r2 = r1.json()[0]
    label = '/label' + ''.join([' ~' + '"' + l + '"' for l in r2['labels']])
    assignees = '/assign ' + ''.join([' @' + n['username'] for n in r2['assignees']])
    milestone = '/milestone %' + '"' + r2['milestone']['title'] + '"'

    link = '/relate'
    r3 = requests.get('http://120.76.207.186/api/v4/projects/848/issues/{}/links'.format(issues_id), headers=headers1)
    r4 = r3.json()
    for a1 in r4:
        # print(a1)
        link = link + ' ' + a1['references']['relative']
    # print(label)
    # print(assignees)
    # print(milestone)
    # print(link)
    _data = label + '\n' + assignees + '\n' + milestone + '\n' + link
    # func_list = importlib.reload(importlib.import_module('func_list.{}'.format('asdf')))
    # module_functions_dict = {name: item for name, item in vars(func_list).items()
    #                          if isinstance(item, types.FunctionType)}
    # # print(module_functions_dict['r_data']())
    # data = module_functions_dict['r_data']()
    # print(type(student.configs.order_by(Config.num.asc())))
    return _data
    # return jsonify({'data':_data})


@api.route('/mon', methods=['get'])
def mon():
    from func_list.mon import a
    b = ','.join(a)

    result1 = requests.get('http://hq.sinajs.cn/rn=1550199258154&list={}'.format(b))
    _d = result1.text.split(';')[:-1]
    l = []
    for g in _d:
        r = g.split(',')
        name = r[0].split('"')[-1]
        value = str(round((float(r[3]) - float(r[2])) / float(r[2]) * 100, 2))
        l.append(name + ':' + value)
    return jsonify(l)


@api.route('/test1_json', methods=['get'])
def test1_json():
    func_list = importlib.reload(importlib.import_module('func_list.{}'.format('asdf1')))
    module_functions_dict = {name: item for name, item in vars(func_list).items()
                             if isinstance(item, types.FunctionType)}
    data = module_functions_dict['r_data']()
    return jsonify(data)


@api.route('/findSqlList')
def find_sql_list():
    import psycopg2

    # database="xiangrikui_production"
    conn = psycopg2.connect(database="team_test", user="xrkadmin", password="xrktest@2016", host="192.168.6.222",
                            port="5432")
    cur = conn.cursor()
    # cur.execute("""SELECT * FROM "xrk_bss"."follows" WHERE maturity='4';""")

    cur.execute("""SELECT * FROM "xrk_bss"."agents" WHERE name='袁一一';""")
    rows = cur.fetchall()
    title_data = [desc[0] for desc in cur.description]
    # sql_list = [{title_data[num]: _row} for row in rows for num, _row in enumerate(row)]
    sql_data = []
    for row in rows:
        _data = {}
        for num, _row in enumerate(row):
            _data[title_data[num]] = _row
        sql_data.append(_data.copy())

    # for row in rows:
    #     print(row)
    conn.close()
    return jsonify({'sql_data': sql_data, 'status': 1, 'title_data': title_data})


@api.route('/test/list', methods=['get'])
def test_list():
    d = [1, 2, 3, 4]

    return jsonify({'msg': d[random.randint(0, 4)]})


@api.route('/test/list1', methods=['POST'])
def test_list1():
    data = request.json
    _id = data.get('d')
    print(_id)

    return jsonify({'status': 1, 'msg': '优化成功'})


@api.route('/test/id', methods=['POST'])
def test_id():
    data = request.json
    _id = data.get('id')
    if _id:
        return jsonify({'status': 1, 'msg': 'id识别成功', 'test_id': _id})
    else:
        return jsonify({'status': 1, 'msg': '请输入id'})

