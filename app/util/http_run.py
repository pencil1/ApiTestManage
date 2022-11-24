import ast
import copy
import json
import types
from app.models import *
from .httprunner.api import HttpRunner
from ..util.global_variable import *
from ..util.utils import encode_object, try_switch_data, is_chinese
import importlib
from app import scheduler
from flask.json import JSONEncoder
from urllib import parse
from .httprunner.parser import parse_data


def parse_quote(value):
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, str):
        if is_chinese(value):
            return parse.quote(value)
        else:
            return value
    else:
        return value


class RunCase(object):
    def __init__(self, project_ids=None):
        self.project_ids = project_ids
        self.pro_environment = None
        self.pro_base_url = None
        self.pro_name = None
        self.new_report_id = None
        self.TEST_DATA = {'testcases': [], 'project_mapping': {'functions': {}, 'variables': {}}}
        self.init_project_data()
        self.result = None

    def init_project_data(self):
        pro_data = Project.query.filter_by(id=self.project_ids).first()
        self.pro_name = pro_data.name
        self.pro_base_url = json.loads(pro_data.environment_list)
        # for pro_data in Project.query.all():
        self.pro_environment = json.loads(pro_data.environment_list)[int(pro_data.environment_choice) - 1]['urls']

        self.pro_config(Project.query.filter_by(id=self.project_ids).first())

    def pro_config(self, project_data):
        """
        把project的配置数据解析出来
        :param project_data:
        :return:
        """

        def project_parse(content):
            """"把数据中引用变量和函数解析出来"""
            return parse_data(content, self.TEST_DATA['project_mapping']['variables'],
                              self.TEST_DATA['project_mapping']['functions'])

        if project_data.func_file:
            self.extract_func(['{}'.format(f[-1].replace('.py', '')) for f in json.loads(project_data.func_file)])

        self.TEST_DATA['project_mapping']['variables'] = {h['key']: project_parse(h['value']) for h in
                                                          json.loads(project_data.variables) if h.get('key')}

        # {headers['key']: parse.quote(headers['value'].replace('%', '&')) for headers in
        #  _header if headers.get('key')} if _header else {}

        self.TEST_DATA['project_mapping']['headers'] = {h['key']: parse_quote(project_parse(h['value'])) for h in
                                                        json.loads(project_data.headers) if h.get('key')}
        # print(111)
        # print(self.TEST_DATA['project_mapping']['headers'])

    def extract_func(self, func_list):
        for f in func_list:
            func_list = importlib.reload(importlib.import_module('func_list.{}'.format(f)))
            module_functions_dict = {name: item for name, item in vars(func_list).items()
                                     if isinstance(item, types.FunctionType)}
            self.TEST_DATA['project_mapping']['functions'].update(module_functions_dict)
        # print(self.TEST_DATA['project_mapping']['functions'])

    def assemble_step(self, api_id=None, step_data=None, pro_base_url=None, status=False):
        """
        :param api_id:
        :param step_data:
        :param pro_base_url:
        :param status: 判断是接口调试(false)or业务用例执行(true)
        :return:
        """
        if status:
            # 为true，获取api基础信息；step_data只包含可改变部分所以还需要api基础信息组合成全新的用例
            api_data = ApiMsg.query.filter_by(id=step_data.api_msg_id).first()
        else:
            # 为false，基础信息和参数信息都在api里面，所以api_case = step_data，直接赋值覆盖
            api_data = ApiMsg.query.filter_by(id=api_id).first()
            step_data = api_data
            # api_data = case_data

        _data = {'name': step_data.name,
                 'request': {'method': api_data.method,
                             'files': {},
                             'data': {}}}
        # _data['request']['headers'] = {h['key']: h['value'] for h in json.loads(api_data.header)
        #                                if h['key']} if json.loads(api_data.header) else {}
        # print(pro_base_url)
        # print(pro_base_url[int(api_data.status_url)])
        # print(api_data.url.split('?')[0])
        # print(api_data.url)
        # print(api_data.status_url)
        # print(api_data.id)
        # print(api_data.url.split('?'))

        if api_data.status_url:
            if (os.getenv('FLASK_CONFIG') or 'default') == 'default':
                # _data['request']['url'] = pro_base_url[int(api_data.status_url)]['value'] + api_data.url.split('?')[0]
                _data['request']['url'] = pro_base_url[int(api_data.status_url)]['value'] + ':1443' + \
                                          api_data.url.split('?')[0]
            else:
                _data['request']['url'] = pro_base_url[int(api_data.status_url)]['value'] + api_data.url.split('?')[0]
        else:
            _data['request']['url'] = api_data.url

        if 'https' in _data['request']['url']:
            _data['request']['verify'] = False

        if step_data.up_func:
            _data['setup_hooks'] = [step_data.up_func]

        if step_data.down_func:
            _data['teardown_hooks'] = [step_data.down_func]

        if step_data.skip:
            _data['skipIf'] = step_data.skip
        if status:
            _data['times'] = step_data.time
            if json.loads(step_data.status_param)[0]:
                if json.loads(step_data.status_param)[1]:
                    _param = json.loads(step_data.param)
                else:
                    _param = json.loads(api_data.param)
            else:
                _param = None

            if json.loads(step_data.status_variables)[0]:
                if json.loads(step_data.status_variables)[1]:
                    _json_variables = step_data.json_variable
                    _variables = json.loads(step_data.variable)
                else:
                    _json_variables = api_data.json_variable
                    _variables = json.loads(api_data.variable)
            else:
                _json_variables = None
                _variables = None

            if json.loads(step_data.status_extract)[0]:
                if json.loads(step_data.status_extract)[1]:
                    _extract = step_data.extract
                else:
                    _extract = api_data.extract
            else:
                _extract = None

            if json.loads(step_data.status_validate)[0]:
                if json.loads(step_data.status_validate)[1]:
                    _validate = step_data.validate
                else:
                    _validate = api_data.validate
            else:
                _validate = None

            if json.loads(step_data.status_header)[0]:
                if json.loads(step_data.status_header)[1]:
                    _header = json.loads(step_data.header)
                else:
                    _header = json.loads(api_data.header)
            else:
                _header = None

        else:
            _param = json.loads(api_data.param)
            _json_variables = api_data.json_variable
            _variables = json.loads(api_data.variable)
            _header = json.loads(api_data.header)
            _extract = api_data.extract
            _validate = api_data.validate

        _data['request']['params'] = {param['key']: param['value'].replace('%', '&') for param in
                                      _param if param.get('key')} if _param else {}

        # parse.quote修复headers带中文报错
        # _data['request']['headers'] = {headers['key']: parse.quote(headers['value'].replace('%', '&')) for headers in
        #                                _header if headers.get('key')} if _header else {}
        step_headers = {headers['key']: parse_quote(headers['value']) for headers in
                        _header if headers.get('key')} if _header else {}

        project_headers = copy.deepcopy(self.TEST_DATA['project_mapping']['headers'])
        # print(project_headers)
        # print(step_headers)
        project_headers.update(step_headers)
        _data['request']['headers'] = project_headers
        # print(_data['request']['headers'])

        # _data['request']['headers'] = copy.deepcopy(self.TEST_DATA['project_mapping']['headers']).update(
        #     {headers['key']: parse.quote(headers['value'].replace('%', '&')) for headers in
        #      _header if headers.get('key')} if _header else {})
        # _data['request']['headers'].update(self.TEST_DATA['project_mapping']['headers'])

        _data['extract'] = [{ext['key']: ext['value']} for ext in json.loads(_extract) if
                            ext.get('key')] if _extract else []

        # for val in json.loads(_validate):
        #     if val.get('key'):
        #         print(val)
        #         ast.literal_eval(val['value'])
        _data['validate'] = [{val['comparator']: [val['key'], try_switch_data(val['value'])]} for val in
                             json.loads(_validate) if val.get('key')] if _validate else []

        if api_data.method == 'GET':
            pass
        elif status and step_data.status_parameters:
            _list_data = []

            for p in json.loads(step_data.parameters):
                _copy_data = copy.deepcopy(_data)
                _copy_data['request'][api_data.variable_type] = p
                _list_data.append(_copy_data)
            # print(_list_data)
            return _list_data

        elif (api_data.variable_type == 'text' or api_data.variable_type == 'data') and _variables:
            # print(_data['request']['headers'])
            if _data['request']['headers'].get('Content-Type') and 'multipart/form-data' in _data['request']['headers'][
                'Content-Type']:
                _data['request']['files'] = ()
                _data['request']['data'] = ()
                for variable in _variables:
                    if variable['param_type'] == 'string' and variable.get('key'):
                        if api_data.variable_type == 'text':
                            _data['request']['files'] += ((variable['key'], (None, variable['value'])),)
                        else:
                            _data['request']['data'] += ((variable['key'], variable['value']),)
                    elif variable['param_type'] == 'file' and variable.get('key'):
                        _data['request']['files'] += ((variable['key'], (
                            variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                            CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])),)

            else:
                for variable in _variables:
                    if variable['param_type'] == 'string' and variable.get('key'):
                        if api_data.variable_type == 'text':
                            _data['request']['files'].update({variable['key']: (None, variable['value'])})
                        else:
                            _data['request']['data'].update({variable['key']: variable['value']})
                    elif variable['param_type'] == 'file' and variable.get('key'):
                        _data['request']['files'].update({variable['key']: (
                            variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                            CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})

        elif api_data.variable_type == 'json':
            if _json_variables:
                # print(_json_variables)
                _data['request']['json'] = json.loads(_json_variables)
        # print(_data)
        # print(1)
        return _data

    def get_api_test(self, api_ids, config_id):
        scheduler.app.logger.info('本次测试的接口id：{}'.format(api_ids))
        _steps = {'teststeps': [], 'config': {'variables': {}}}
        if config_id:
            config_data = Config.query.filter_by(id=config_id).first()
            _config = json.loads(config_data.variables) if config_id else []
            _steps['config']['variables'].update({v['key']: v['value'] for v in _config if v['key']})
            self.extract_func(['{}'.format(f[-1].replace('.py', '')) for f in json.loads(config_data.func_address)])

        _steps['teststeps'] = [self.assemble_step(api_id, None, self.pro_environment, False) for api_id in api_ids]
        self.TEST_DATA['testcases'].append(_steps)

    def get_case_step_test(self, step_id):
        # 获取用例中的单个步骤拼接数据进行调试
        scheduler.app.logger.info('本次测试的步骤id：{}'.format(step_id))
        step_data = CaseData.query.filter_by(id=step_id).first()
        case_data = Case.query.filter_by(id=step_data.case_id).first()
        if case_data.environment == -1 or not case_data.environment:
            url_environment = self.pro_environment
        else:
            url_environment = self.pro_base_url[case_data.environment]

        _steps = {'teststeps': [], 'config': {'variables': {}, 'name': ''}}
        _steps['config']['name'] = case_data.name

        # 获取业务集合的配置数据
        _config = json.loads(case_data.variable) if case_data.variable else []
        _steps['config']['variables'].update({v['key']: v['value'] for v in _config if v['key']})

        module_functions_dict = {}
        for f in ['{}'.format(f[-1].replace('.py', '')) for f in json.loads(case_data.func_address)]:
            func_list = importlib.reload(importlib.import_module('func_list.{}'.format(f)))
            # func_list = importlib.reload(importlib.import_module('debugtalk'))
            module_functions_dict.update({name: item for name, item in vars(func_list).items()
                                          if isinstance(item, types.FunctionType)})

        _steps['config']['functions'] = module_functions_dict
        # # 获取需要导入的函数
        # self.extract_func(['{}'.format(f[-1].replace('.py', '')) for f in json.loads(case_data.func_address)])
        _steps_data = self.assemble_step(None, step_data, url_environment, True)
        if isinstance(_steps_data, list):
            _steps['teststeps'] += _steps_data
        else:
            _steps['teststeps'].append(_steps_data)
        self.TEST_DATA['testcases'].append(_steps)

    def get_case_test_data(self, case_id):

        case_data = Case.query.filter_by(id=case_id).first()
        # print(case_id)
        # case_times = case_data.times if case_data.times else 1
        if case_data.environment == -1 or not case_data.environment:
            url_environment = self.pro_environment
        else:
            url_environment = self.pro_base_url[case_data.environment]
        # for s in range(case_times):
        one_case = {'teststeps': [], 'config': {'variables': {}, 'name': ''}}
        one_case['config']['name'] = case_data.name

        # 获取业务集合的配置数据
        _config = json.loads(case_data.variable) if case_data.variable else []
        one_case['config']['variables'].update({v['key']: v['value'] for v in _config if v['key']})

        module_functions_dict = {}
        for f in ['{}'.format(f[-1].replace('.py', '')) for f in json.loads(case_data.func_address)]:
            func_list = importlib.reload(importlib.import_module('func_list.{}'.format(f)))
            # func_list = importlib.reload(importlib.import_module('debugtalk'))
            module_functions_dict.update({name: item for name, item in vars(func_list).items()
                                          if isinstance(item, types.FunctionType)})

        one_case['config']['functions'] = module_functions_dict
        # # 获取需要导入的函数
        # self.extract_func(['{}'.format(f[-1].replace('.py', '')) for f in json.loads(case_data.func_address)])
        # print(case_id)
        # print(CaseData.query.filter_by(case_id=case_id).order_by(CaseData.num.asc()).all())
        for _step in CaseData.query.filter_by(case_id=case_id).order_by(CaseData.num.asc()).all():
            if _step.status == 'true':  # 判断用例状态，是否执行
                _steps_data = self.assemble_step(None, _step, url_environment, True)
                if isinstance(_steps_data, list):
                    one_case['teststeps'] += _steps_data
                else:
                    one_case['teststeps'].append(_steps_data)
        return one_case

    def get_case_test(self, case_ids):
        scheduler.app.logger.info('本次测试的用例id：{}'.format(case_ids))
        for case_id in case_ids:
            id_list = []

            def get_all_case_id(i):
                # 获取待测用例下所有的前置用例id
                _d = Case.query.filter_by(id=i).first()
                id_list.append(i)
                if not _d.up_case_id:
                    return
                else:
                    for _i in json.loads(_d.up_case_id):
                        get_all_case_id(_i)

            get_all_case_id(case_id)
            # print(id_list)
            _data = {'teststeps': [], 'config': {'variables': {}, 'name': '', 'functions': {}}}
            for _case_data in [self.get_case_test_data(i) for i in id_list[::-1]]:
                _data['config']['variables'].update(_case_data['config']['variables'])
                _data['config']['functions'].update(_case_data['config']['functions'])
                _data['config']['name'] = _case_data['config']['name']
                _data['teststeps'] += _case_data['teststeps']
            self.TEST_DATA['testcases'].append(_data)

    def insert_api_log(self):
        # print(json.loads(self.result)['details'])
        for r1 in json.loads(self.result)['details']:
            for r2 in r1['records']:
                try:
                    new_log = Logs(log_type=2,
                                   project_id=self.project_ids,
                                   project_name=self.pro_name,
                                   api='/' + r2['meta_datas']['data'][0]['request']['url'].split('/', 3)[-1].split('?')[
                                       0],
                                   api_status=r2['status'],
                                   report_id=self.new_report_id)
                    db.session.add(new_log)
                except:
                    pass

        db.session.commit()

    def build_report(self, jump_res, case_ids, performer):
        # if self.run_type and self.make_report:
        new_report = Report(performer=performer,
                            case_names=','.join(
                                [Case.query.filter_by(id=scene_id).first().name for scene_id in case_ids]),
                            project_id=self.project_ids, read_status='待阅',
                            result='通过' if json.loads(jump_res)['success'] else '失败')
        db.session.add(new_report)
        db.session.commit()

        self.new_report_id = new_report.id

        def dict_c(d):
            # 存在content返回数据特别多情况，直接砍掉
            if isinstance(d, dict):
                for d1 in d:
                    if d1 == 'content':
                        if len(d[d1]) > 10000:
                            d[d1] = d[d1][:100]
                    dict_c(d[d1])
            else:
                if isinstance(d, list):
                    for d2 in d:
                        dict_c(d2)
            return d

        jump_res = dict_c(jump_res)

        with open('{}{}.txt'.format(REPORT_ADDRESS, self.new_report_id), 'w') as f:
            f.write(jump_res)

    def run_case(self):
        scheduler.app.logger.info('测试数据：{}'.format(self.TEST_DATA))
        # res = main_ate(self.TEST_DATA)
        # print(self.TEST_DATA)
        runner = HttpRunner()

        runner.run(self.TEST_DATA)
        self.result = json.dumps(runner._summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
        return self.result
