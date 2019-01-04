import copy
import json
from app.models import *
from httprunner.api import HttpRunner
from ..util.global_variable import *
from ..util.utils import merge_config, encode_object
import importlib
import types


def main_ate(cases):
    runner = HttpRunner()
    runner.run(cases)
    summary = runner._summary
    print(summary)
    return summary


class RunCase(object):
    def __init__(self, project_ids=None):
        self.project_ids = project_ids
        self.pro_config_data = None
        self.pro_base_url = None
        self.run_type = False  # 判断是接口调试(false)or业务用例执行(true)
        self.make_report = True
        self.new_report_id = None
        self.functions = dict()
        self.test_data = None
        self.init_project_data()

    def init_project_data(self):
        self.pro_config_data = self.pro_config(Project.query.filter_by(id=self.project_ids).first())
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
        self.pro_base_url = pro_base_url

    @staticmethod
    def pro_config(project_data):
        """
        把project的配置数据解析出来
        :param project_data:
        :return:
        """
        pro_cfg_data = {'config': {'name': 'config_name', 'request': {}, 'output': []},
                        'teststeps': [],
                        'name': 'config_name'}

        pro_cfg_data['config']['request']['headers'] = {h['key']: h['value'] for h in
                                                        json.loads(project_data.headers) if h.get('key')}

        pro_cfg_data['config']['variables'] = json.loads(project_data.variables)
        return pro_cfg_data

    def assemble_step(self, case_data, pro_base_url):
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

        # if 'https' in temp_case_data['request']['url']:
        #     temp_case_data['request']['verify'] = False
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
            temp_case_data['times'] = case_data.time

        if not self.run_type or json.loads(case_data.status_param)[0]:
            if not self.run_type or json.loads(case_data.status_param)[1]:
                _param = json.loads(case_data.param)
            else:
                _param = json.loads(api_case.param)
            temp_case_data['request']['params'] = {param['key']: param['value'].replace('%', '&') for param in
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
            elif api_case.variable_type == 'text':
                for variable in _variables:
                    if variable['param_type'] == 'string' and variable.get('key'):
                        temp_case_data['request']['files'].update({variable['key']: (None, variable['value'])})
                    elif variable['param_type'] == 'file' and variable.get('key'):
                        temp_case_data['request']['files'].update({variable['key']: (
                            variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                            CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})

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

        if not self.run_type or json.loads(case_data.status_validate)[0]:
            if not self.run_type or json.loads(case_data.status_validate)[1]:
                _validate_temp = case_data.validate
            else:
                _validate_temp = api_case.validate
            temp_case_data['validate'] = [{val['comparator']: [val['key'], val['value']]} for val in
                                          json.loads(_validate_temp) if val.get('key')]

            temp_case_data['output'] = ['token']

        return temp_case_data

    def get_api_test(self, api_data, config_id):
        _d = {'testcases': [], 'project_mapping': {'functions': {}}}
        _temp_config = copy.deepcopy(self.pro_config_data)
        config_data = Config.query.filter_by(id=config_id).first()
        _config = json.loads(config_data.variables) if config_id else []
        if config_id:
            for p in ['func_list.{}'.format(f.replace('.py', '')) for f in json.loads(config_data.func_address)]:
                func_list = importlib.reload(importlib.import_module(p))
                module_functions_dict = {name: item for name, item in vars(func_list).items()
                                         if isinstance(item, types.FunctionType)}
                self.functions.update(module_functions_dict)
        _temp_config = merge_config(_temp_config, _config)
        _temp_config['teststeps'] = [self.assemble_step(case, self.pro_base_url) for case in api_data]
        _d['testcases'].append(_temp_config)
        _d['project_mapping']['functions'] = self.functions
        return _d

    def get_case_test(self, case_ids):
        _d = {'testcases': [], 'project_mapping': {'functions': {}}}

        for case_id in case_ids:
            case_data = Case.query.filter_by(id=case_id).first()
            case_times = case_data.times if case_data.times else 1
            for s in range(case_times):
                _temp_config = copy.deepcopy(self.pro_config_data)
                _temp_config['config']['name'] = case_data.name

                # 获取需要导入的函数
                for p in ['func_list.{}'.format(f.replace('.py', '')) for f in json.loads(case_data.func_address)]:
                    func_list = importlib.reload(importlib.import_module(p))
                    module_functions_dict = {name: item for name, item in vars(func_list).items()
                                             if isinstance(item, types.FunctionType)}
                    self.functions.update(module_functions_dict)

                # 获取业务集合的配置数据
                scene_config = json.loads(case_data.variable) if case_data.variable else []

                # 合并公用项目配置和业务集合配置
                _temp_config = merge_config(_temp_config, scene_config)
                for api_case in CaseData.query.filter_by(case_id=case_id).order_by(CaseData.num.asc()).all():
                    if api_case.status == 'true':  # 判断用例状态，是否执行
                        _temp_config['teststeps'].append(self.assemble_step(api_case, self.pro_base_url))
                _d['testcases'].append(_temp_config)
        _d['project_mapping']['functions'] = self.functions
        return _d

    def build_report(self, jump_res, case_ids):
        # if self.run_type and self.make_report:
        new_report = Report(
            case_names=','.join([Case.query.filter_by(id=scene_id).first().name for scene_id in case_ids]),
            project_id=self.project_ids, read_status='待阅')
        db.session.add(new_report)
        db.session.commit()

        self.new_report_id = new_report.id
        with open('{}{}.txt'.format(REPORT_ADDRESS, self.new_report_id), 'w') as f:
            f.write(jump_res)

    def run_case(self, test_cases):
        now_time = datetime.datetime.now()
        # current_app.logger.info('begin to run cases')
        # current_app.logger.info('cases message: {}'.format(d))
        res = main_ate(test_cases)

        res['time']['duration'] = "%.2f" % res['time']['duration']
        # res['stat']['successes_1'] = res['stat']['successes']
        # res['stat']['failures_1'] = res['stat']['failures']
        # res['stat']['errors_1'] = res['stat']['errors']
        # res['stat']['teststeps']['successes'] = "{} ({}%)".format(res['stat']['teststeps']['successes'],
        #                                                           int(res['stat']['successes'] / res['stat'][
        #                                                               'testsRun'] * 100))
        # res['stat']['teststeps']['failures'] = "{} ({}%)".format(res['stat']['failures'],
        #                                                          int(res['stat']['failures'] / res['stat'][
        #                                                              'testsRun'] * 100))
        # res['stat']['teststeps']['errors'] = "{} ({}%)".format(res['stat']['errors'],
        #                                                        int(res['stat']['errors'] / res['stat'][
        #                                                            'testsRun'] * 100))
        # res['stat']['successes_scene'] = 0
        # res['stat']['failures_scene'] = 0
        # for num_1, res_1 in enumerate(res['details']):
        #     if res_1['success']:
        #         res['stat']['successes_scene'] += 1
        #     else:
        #         res['stat']['failures_scene'] += 1

        res['time']['start_at'] = now_time.strftime('%Y/%m/%d %H:%M:%S')
        jump_res = json.dumps(res, ensure_ascii=False, default=encode_object)

        return jump_res
