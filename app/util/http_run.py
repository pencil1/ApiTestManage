import copy
import json

from app.models import *
from httprunner import HttpRunner
from ..util.global_variable import *
from ..util.utils import merge_config, encode_object
from httprunner import (loader, parser, utils)
import importlib


class MyHttpRunner(HttpRunner):
    """
    修改HttpRunner，用例初始化时导入函数
    """

    def __init__(self):
        super(MyHttpRunner, self).__init__()

    def parse_tests(self, testcases, variables_mapping=None):
        """ parse testcases configs, including variables/parameters/name/request.

        Args:
            testcases (list): testcase list, with config unparsed.
            variables_mapping (dict): if variables_mapping is specified, it will override variables in config block.

        Returns:
            list: parsed testcases list, with config variables/parameters/name/request parsed.

        """
        self.exception_stage = "parse tests"
        variables_mapping = variables_mapping or {}

        parsed_testcases_list = []
        for testcase in testcases:
            # parse config parameters
            config_parameters = testcase.setdefault("config", {}).pop("parameters", [])

            cartesian_product_parameters_list = parser.parse_parameters(
                config_parameters,
                self.project_mapping["debugtalk"]["variables"],
                self.project_mapping["debugtalk"]["functions"]
            ) or [{}]

            for parameter_mapping in cartesian_product_parameters_list:
                testcase_dict = testcase
                config = testcase_dict.setdefault("config", {})

                testcase_dict["config"]["functions"] = {}

                # imported_module = importlib.reload(importlib.import_module('func_list.build_in'))
                # testcase_dict["config"]["functions"].update(loader.load_python_module(imported_module)["functions"])

                if config.get('import_module_functions'):
                    for f in config.get('import_module_functions'):
                        imported_module = importlib.reload(importlib.import_module(f))
                        debugtalk_module = loader.load_python_module(imported_module)
                        testcase_dict["config"]["functions"].update(debugtalk_module["functions"])
                testcase_dict["config"]["functions"].update(self.project_mapping["debugtalk"]["functions"])
                # self.project_mapping["debugtalk"]["functions"].update(debugtalk_module["functions"])
                raw_config_variables = config.get("variables", [])
                parsed_config_variables = parser.parse_data(
                    raw_config_variables,
                    self.project_mapping["debugtalk"]["variables"],
                    testcase_dict["config"]["functions"])

                # priority: passed in > debugtalk.py > parameters > variables
                # override variables mapping with parameters mapping
                config_variables = utils.override_mapping_list(
                    parsed_config_variables, parameter_mapping)
                # merge debugtalk.py module variables
                config_variables.update(self.project_mapping["debugtalk"]["variables"])
                # override variables mapping with passed in variables_mapping
                config_variables = utils.override_mapping_list(
                    config_variables, variables_mapping)

                testcase_dict["config"]["variables"] = config_variables

                # parse config name
                testcase_dict["config"]["name"] = parser.parse_data(
                    testcase_dict["config"].get("name", ""),
                    config_variables,
                    self.project_mapping["debugtalk"]["functions"]
                )

                # parse config request
                testcase_dict["config"]["request"] = parser.parse_data(
                    testcase_dict["config"].get("request", {}),
                    config_variables,
                    self.project_mapping["debugtalk"]["functions"]
                )
                # put loaded project functions to config
                # testcase_dict["config"]["functions"] = self.project_mapping["debugtalk"]["functions"]
                parsed_testcases_list.append(testcase_dict)
        return parsed_testcases_list


def main_ate(cases):
    runner = MyHttpRunner().run(cases)
    summary = runner.summary
    return summary


class RunCase(object):
    def __init__(self, project_names=None, case_ids=None, api_data=None, config_id=None):
        self.project_names = project_names
        self.case_ids = case_ids
        self.config_id = config_id
        self.api_data = api_data
        self.project_data = Project.query.filter_by(name=self.project_names).first()
        self.project_id = self.project_data.id
        self.run_type = False  # 判断是接口调试(false)or业务用例执行(true)
        self.make_report = True
        self.new_report_id = None
        self.temp_extract = list()

    def project_case(self):
        if self.project_names and not self.case_ids and not self.api_data:
            case_id = [s.id for s in Case.query.filter_by(project_id=self.project_id).order_by(Case.num.asc()).all()]
            all_case_data = []
            for c in case_id:
                for c1 in CaseData.query.filter_by(scene_id=c).order_by(CaseData.num.asc()).all():
                    all_case_data.append(c1)
            self.run_type = True
            return all_case_data
        else:
            return None

    # def scene_case(self):
    #     if self.scene_ids:
    #         scene_id = [Scene.query.filter_by(name=n, project_id=self.project_id).first().id for n in self.scene_ids]
    #         self.run_type = True
    #         return scene_id
    #     else:
    #         return None
    #
    # def one_case(self):
    #     if self.project_names and not self.scene_ids and self.case_data:
    #         self.run_type = False
    #         return self.case_data
    #     else:
    #         return None

    @staticmethod
    def pro_config(project_data):
        """
        把project的配置数据解析出来
        :param project_data:
        :return:
        """
        pro_cfg_data = {'config': {'name': 'config_name', 'request': {}, 'output': []}, 'teststeps': [],
                        'name': 'config_name'}

        pro_cfg_data['config']['request']['headers'] = {h['key']: h['value'] for h in
                                                        json.loads(project_data.headers) if h.get('key')}

        pro_cfg_data['config']['variables'] = json.loads(project_data.variables)
        return pro_cfg_data

    def get_test_case(self, case_data, pro_base_url):
        if self.run_type:
            # 为true，获取api基础信息；case只包含可改变部分所以还需要api基础信息组合成全新的用例
            api_case = ApiMsg.query.filter_by(id=case_data.api_msg_id).first()
        else:
            # 为false，基础信息和参数信息都在api里面，所以api_case = case_data，直接赋值覆盖
            api_case = case_data

        temp_case_data = {'name': case_data.name,
                          'request': {'method': api_case.method,
                                      'files': {},
                                      'data': {}}}
        if json.loads(api_case.header):
            temp_case_data['request']['headers'] = {h['key']: h['value'] for h in json.loads(api_case.header)
                                                    if h['key']}

        if api_case.status_url != '-1':
            temp_case_data['request']['url'] = pro_base_url['{}'.format(api_case.project_id)][
                                                   int(api_case.status_url)] + api_case.url.split('?')[0]
        else:
            temp_case_data['request']['url'] = api_case.url

        # if api_case.func_address:
        #     print(api_case.func_address)
        #     temp_case_data['import_module_functions'] = [
        #         'func_list.{}'.format(f.replace('.py', '')) for f in json.loads(api_case.func_address)]
        # if self.run_type:
        if not self.run_type:
            if api_case.up_func:
                temp_case_data['setup_hooks'] = [api_case.up_func]
            if api_case.down_func:
                temp_case_data['teardown_hooks'] = [api_case.down_func]
        else:
            if case_data.up_func:
                temp_case_data['setup_hooks'] = [case_data.up_func]
            if case_data.down_func:
                temp_case_data['teardown_hooks'] = [case_data.down_func]

        if not self.run_type or json.loads(case_data.status_param)[0]:
            if not self.run_type or json.loads(case_data.status_param)[1]:
                _param = json.loads(case_data.param)
            else:
                _param = json.loads(api_case.param)
            temp_case_data['request']['params'] = {param['key']: param['value'] for param in
                                                   _param if param.get('key')}

        if not self.run_type or json.loads(case_data.status_variables)[0]:
            if not self.run_type or json.loads(case_data.status_variables)[1]:
                _json_variables = case_data.json_variable
                _variables = json.loads(case_data.variable)

            else:
                _json_variables = api_case.json_variable
                _variables = json.loads(case_data.variable)

            if api_case.method == 'GET':
                pass
            elif api_case.variable_type == 'data':
                for variable in _variables:
                    if variable['param_type'] == 'string' and variable.get('key'):
                        temp_case_data['request']['data'].update({variable['key']: variable['value']})
                    elif variable['param_type'] == 'file' and variable.get('key'):
                        temp_case_data['request']['files'].update({variable['key']: (
                            variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                            CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})
                        # temp_case_data['request']['files'].update({variable['key']: (
                        #     variable['value'].split('/')[-1], "open({}, 'rb')".format(variable['value']),
                        #     CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})

                        # temp_case_data['request']['files'].update({variable['key']: (
                        #     variable['value'].split('/')[-1], '${' + 'open_file({})'.format(variable['value']) + '}',
                        #     CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})

            elif api_case.variable_type == 'json':
                if _json_variables:
                    temp_case_data['request']['json'] = json.loads(_json_variables)
                # temp_case_data['request']['json'] = _variables

        if not self.run_type or json.loads(case_data.status_extract)[0]:
            if not self.run_type or json.loads(case_data.status_extract)[1]:
                _extract_temp = case_data.extract
            else:
                _extract_temp = api_case.extract

            temp_case_data['extract'] = [{ext['key']: ext['value']} for ext in json.loads(_extract_temp) if
                                         ext.get('key')]
            self.temp_extract += [ext.get('key') for ext in json.loads(_extract_temp) if ext.get('key')]

        if not self.run_type or json.loads(case_data.status_validate)[0]:
            if not self.run_type or json.loads(case_data.status_validate)[1]:
                _validate_temp = case_data.validate
            else:
                _validate_temp = api_case.validate
            temp_case_data['validate'] = [{val['comparator']: [val['key'], val['value']]} for val in
                                          json.loads(_validate_temp) if val.get('key')]

            temp_case_data['output'] = ['token']

        return temp_case_data

    def all_cases_data(self):
        temp_case = []
        pro_config = self.pro_config(self.project_data)

        # 获取项目中4个基础url
        # pro_base_url = {'0': self.project_data.host, '1': self.project_data.host_two,
        #                 '2': self.project_data.host_three, '3': self.project_data.host_four}
        pro_base_url = {}
        for pro_data in Project.query.all():
            if pro_data.environment_choice == 'first':
                pro_base_url['{}'.format(pro_data.id)] = json.loads(pro_data.host)
            elif pro_data.environment_choice == 'second':
                pro_base_url['{}'.format(pro_data.id)] = json.loads(pro_data.host_two)
            if pro_data.environment_choice == 'third':
                pro_base_url['{}'.format(pro_data.id)] = json.loads(pro_data.host_three)
            if pro_data.environment_choice == 'fourth':
                pro_base_url['{}'.format(pro_data.id)] = json.loads(pro_data.host_four)
        if self.case_ids:
            for case_id in self.case_ids:
                case_data = Case.query.filter_by(id=case_id).first()
                case_times = case_data.times if case_data.times else 1
                for s in range(case_times):
                    _temp_config = copy.deepcopy(pro_config)
                    _temp_config['config']['name'] = case_data.name

                    # 获取需要导入的函数文件数据
                    _temp_config['config']['import_module_functions'] = ['func_list.{}'.format(
                        f.replace('.py', '')) for f in json.loads(case_data.func_address)]

                    # 获取业务集合的配置数据
                    scene_config = json.loads(case_data.variable) if case_data.variable else []

                    # 合并公用项目配置和业务集合配置
                    _temp_config = merge_config(_temp_config, scene_config)
                    for api_case in CaseData.query.filter_by(case_id=case_id).order_by(CaseData.num.asc()).all():
                        if api_case.status == 'true':  # 判断用例状态，是否执行
                            for t in range(api_case.time):  # 获取用例执行次数，遍历添加
                                _temp_config['teststeps'].append(self.get_test_case(api_case, pro_base_url))
                    temp_case.append(_temp_config)
            return temp_case

        if self.api_data:
            _temp_config = copy.deepcopy(pro_config)
            config_data = Config.query.filter_by(id=self.config_id).first()
            _config = json.loads(config_data.variables) if self.config_id else []
            if self.config_id:
                _temp_config['config']['import_module_functions'] = ['func_list.{}'.format(
                    f.replace('.py', '')) for f in json.loads(config_data.func_address)]

            _temp_config = merge_config(_temp_config, _config)
            _temp_config['teststeps'] = [self.get_test_case(case, pro_base_url) for case in self.api_data]
            _temp_config['config']['output'] += copy.deepcopy(self.temp_extract)
            return _temp_config
            # return temp_case

    def run_case(self):
        now_time = datetime.datetime.now()

        if self.run_type and self.make_report:
            new_report = Report(
                name=','.join([Case.query.filter_by(id=scene_id).first().name for scene_id in self.case_ids]),
                data='{}.txt'.format(now_time.strftime('%Y/%m/%d %H:%M:%S')),
                belong_pro=self.project_names, read_status='待阅')
            db.session.add(new_report)
            db.session.commit()
        d = self.all_cases_data()
        res = main_ate(d)

        res['time']['duration'] = "%.2f" % res['time']['duration']
        res['stat']['successes_1'] = res['stat']['successes']
        res['stat']['failures_1'] = res['stat']['failures']
        res['stat']['errors_1'] = res['stat']['errors']
        res['stat']['successes'] = "{} ({}%)".format(res['stat']['successes'],
                                                     int(res['stat']['successes'] / res['stat']['testsRun'] * 100))
        res['stat']['failures'] = "{} ({}%)".format(res['stat']['failures'],
                                                    int(res['stat']['failures'] / res['stat']['testsRun'] * 100))
        res['stat']['errors'] = "{} ({}%)".format(res['stat']['errors'],
                                                  int(res['stat']['errors'] / res['stat']['testsRun'] * 100))
        res['stat']['successes_scene'] = 0
        res['stat']['failures_scene'] = 0
        for num_1, res_1 in enumerate(res['details']):
            if res_1['success']:
                res['stat']['successes_scene'] += 1
            else:
                res['stat']['failures_scene'] += 1

        res['time']['start_at'] = now_time.strftime('%Y/%m/%d %H:%M:%S')
        print(res)
        jump_res = json.dumps(res, ensure_ascii=False, default=encode_object)
        if self.run_type and self.make_report:
            self.new_report_id = Report.query.filter_by(
                data='{}.txt'.format(now_time.strftime('%Y/%m/%d %H:%M:%S'))).first().id
            with open('{}{}.txt'.format(REPORT_ADDRESS, self.new_report_id), 'w') as f:
                f.write(jump_res)
        return jump_res
