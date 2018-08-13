import copy
from app.models import *
from httprunner.task import HttpRunner
from httprunner.testcase import *
from ..util.global_variable import *
import platform
from ..util.utils import merge_config


def main_ate(cases):
    logger.setup_logger('INFO')
    # importlib.reload(httprunner)
    # print(cases)
    # importlib.reload(importlib.import_module('func_list.build_in_func'))
    runner = HttpRunner().run(cases)
    summary = runner.summary
    return summary


class RunCase(object):
    def __init__(self, project_names=None, scene_names=None, case_data=None):
        self.project_names = project_names
        self.scene_names = scene_names
        self.case_data = case_data
        self.project_id = Project.query.filter_by(name=self.project_names).first().id
        self.project_config = Project.query.filter_by(id=self.project_id).first()
        self.pro_cfg_data = dict()
        self.run_type = False
        self.all_case_data = self.project_case() or self.scene_case() or self.one_case()
        self.new_report_id = ''

    def project_case(self):
        if self.project_names and not self.scene_names and not self.case_data:
            scene_id = [s.id for s in Scene.query.filter_by(project_id=self.project_id).order_by(Scene.num.asc()).all()]
            all_case_data = []
            for c in scene_id:
                for c1 in ApiCase.query.filter_by(scene_id=c).order_by(ApiCase.num.asc()).all():
                    all_case_data.append(c1)
            self.run_type = True
            return all_case_data
        else:
            return None

    def scene_case(self):
        if self.scene_names:
            scene_id = [Scene.query.filter_by(name=n).first().id for n in self.scene_names]
            # all_case_data = []
            # for c in scene_id:
            #     for c1 in ApiCase.query.filter_by(scene_id=c).order_by(ApiCase.num.asc()).all():
            #         all_case_data.append(c1)
            self.run_type = True
            return scene_id
        else:
            return None

    def one_case(self):
        if self.project_names and not self.scene_names and self.case_data:
            self.run_type = False
            return self.case_data
        else:
            return None

    @staticmethod
    def pro_config(project_id):
        pro_cfg_data = {'config': {'name': 'config_name', 'request': {}}, 'testcases': [], 'name': 'config_name'}
        project_config = Project.query.filter_by(id=project_id).first()

        pro_cfg_data['config']['request']['headers'] = {h['key']: h['value'] for h in
                                                        json.loads(project_config.headers) if h.get('key')}

        pro_cfg_data['config']['variables'] = json.loads(project_config.variables)
        return pro_cfg_data

    def get_case(self, scene_case, pro_config):
        if self.run_type:
            api_case = ApiMsg.query.filter_by(id=scene_case.apiMsg_id).first()
        else:
            api_case = scene_case

        temp_case_data = {'name': scene_case.name,
                          'request': {'method': api_case.method,
                                      'files': {},
                                      'data': {}}}
        if scene_case.up_func:
            temp_case_data['setup_hooks'] = [scene_case.up_func]
        if scene_case.down_func:
            temp_case_data['teardown_hooks'] = [scene_case.down_func]
        if json.loads(api_case.headers):
            temp_case_data['request']['headers'] = {h['key']: h['value'] for h in json.loads(api_case.headers)
                                                    if h['key']}

        temp_case_data['request']['url'] = getattr(pro_config, HOST[api_case.status_url]) + api_case.url

        if api_case.func_address:
            temp_case_data['import_module_functions'] = [
                'func_list.{}'.format(api_case.func_address.replace('.py', ''))]
        # if self.run_type:
        if not self.run_type or json.loads(scene_case.status_variables)[0]:
            if not self.run_type or json.loads(scene_case.status_variables)[1]:
                _variables = json.loads(scene_case.variables)

            else:
                _variables = json.loads(api_case.variables)

            if api_case.method == 'GET':
                temp_case_data['request']['params'] = {variable['key']: variable['value'] for variable in
                                                       _variables if variable.get('key')}
            else:
                if api_case.variable_type == 'data':
                    for variable in _variables:
                        if variable['param_type'] == 'string' and variable.get('key'):
                            temp_case_data['request']['data'].update({variable['key']: variable['value']})
                        elif variable['param_type'] == 'file' and variable.get('key'):
                            temp_case_data['request']['files'].update({variable['key']: (
                                variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                                CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})

                else:
                    temp_case_data['request']['json'] = _variables

        if not self.run_type or json.loads(scene_case.status_extract)[0]:
            if not self.run_type or json.loads(scene_case.status_extract)[1]:
                _extract_temp = scene_case.extract
            else:
                _extract_temp = api_case.extract

            temp_case_data['extract'] = [{ext['key']: ext['value']} for ext in json.loads(_extract_temp) if
                                         ext.get('key')]

        if not self.run_type or json.loads(scene_case.status_validate)[0]:
            if not self.run_type or json.loads(scene_case.status_validate)[1]:
                _validate_temp = scene_case.validate
            else:
                _validate_temp = api_case.validate
            temp_case_data['validate'] = [{val['comparator']: [val['key'], val['value']]} for val in
                                          json.loads(_validate_temp) if val.get('key')]

        return temp_case_data

    def all_cases_data(self):
        temp_case = []
        if self.scene_names:
            scene_ids = [Scene.query.filter_by(name=n).first().id for n in self.scene_names]
            for scene in scene_ids:
                scene_data = Scene.query.filter_by(id=scene).first()
                pro_config = self.pro_config(scene_data.project_id)
                pro_config['config']['name'] = scene_data.name

                if scene_data.func_address:
                    pro_config['config']['import_module_functions'] = [
                        'func_list.{}'.format(scene_data.func_address.replace('.py', ''))]

                if scene_data.variables:
                    scene_config = json.loads(scene_data.variables)
                else:
                    scene_config = []
                pro_config = merge_config(pro_config, scene_config)

                for case in ApiCase.query.filter_by(scene_id=scene).order_by(ApiCase.num.asc()).all():
                    if case.status == 'true':
                        pro_config['testcases'].append(
                            self.get_case(case, Project.query.filter_by(id=scene_data.project_id).first()))
                temp_case.append(copy.deepcopy(pro_config))
            return temp_case
        if self.case_data:
            pro_config = self.pro_config(self.project_id)
            config_data = SceneConfig.query.filter_by(name=self.case_data[0]).first()
            if not self.case_data[0]:
                _config = []
            else:
                _config = json.loads(config_data.variables)
            if config_data:
                if config_data.func_address:
                    pro_config['config']['import_module_functions'] = [
                        'func_list.{}'.format(config_data.func_address.replace('.py', ''))]

            pro_config = merge_config(pro_config, _config)
            for case in self.case_data[1]:
                pro_config['testcases'].append(
                    self.get_case(case, Project.query.filter_by(id=self.project_id).first()))
            temp_case.append(copy.deepcopy(pro_config))
            return temp_case

    def run_case(self):
        now_time = datetime.datetime.now()

        if self.run_type:
            new_report = Report(name=','.join(self.scene_names),
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
            for num_2, rec_2 in enumerate(res_1['records']):
                if isinstance(rec_2['meta_data']['response']['content'], bytes):
                    rec_2['meta_data']['response']['content'] = bytes.decode(rec_2['meta_data']['response']['content'])
                if rec_2['meta_data']['request'].get('body'):
                    if isinstance(rec_2['meta_data']['request']['body'], bytes):
                        rec_2['meta_data']['request']['body'] = bytes.decode(rec_2['meta_data']['request']['body'])

                if rec_2['meta_data']['response'].get('cookies'):
                    rec_2['meta_data']['response']['cookies'] = dict(
                        res['details'][0]['records'][0]['meta_data']['response']['cookies'])
                    # for num, rec in enumerate(res['details'][0]['records']):
                    # try:
                    # if not rec['meta_data'].get('url'):
                    #     rec['meta_data']['url'] = self.temporary_url[num] + '\n(url请求失败，这为原始url，)'
                    # if 'Linux' in platform.platform():
                    #     rec['meta_data']['response_time(ms)'] = rec['meta_data'].get('response_time_ms')
                    # if rec['meta_data'].get('response_headers'):
                    #     rec['meta_data']['response_headers'] = dict(res['records'][num]['meta_data']['response_headers'])
                    # if rec['meta_data'].get('request_headers'):
                    #     rec['meta_data']['request_headers'] = dict(res['records'][num]['meta_data']['request_headers'])
                    # if rec['meta_data'].get('request_body'):
                    #     if isinstance(rec['meta_data']['request_body'], bytes):
                    #         if b'filename=' in rec['meta_data']['request_body']:
                    #             rec['meta_data']['request_body'] = '暂不支持显示文件上传的request_body'
                    #         else:
                    #             rec['meta_data']['request_body'] = rec['meta_data']['request_body'].decode('unicode-escape')

                    # if rec['meta_data'].get('response_body'):
                    #     if isinstance(rec['meta_data']['response_body'], bytes):
                    #         rec['meta_data']['response_body'] = bytes.decode(rec['meta_data']['response_body'])
                    # if not rec['meta_data'].get('response_headers'):
                    #     rec['meta_data']['response_headers'] = 'None'

        res['time']['start_at'] = now_time.strftime('%Y/%m/%d %H:%M:%S')
        jump_res = json.dumps(res, ensure_ascii=False)
        if self.run_type:
            self.new_report_id = Report.query.filter_by(
                data='{}.txt'.format(now_time.strftime('%Y/%m/%d %H:%M:%S'))).first().id
            with open('{}{}.txt'.format(REPORT_ADDRESS, self.new_report_id), 'w') as f:
                f.write(jump_res)
        return jump_res
