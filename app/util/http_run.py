import copy
import importlib

import time

from app.models import *
from httprunner.task import HttpRunner
# import httprunner
from httprunner.testcase import *
from ..util.global_variable import *
import platform


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
        if json.loads(project_config.headers):
            # self.all_data['config']['request']['headers'] = {}
            pro_cfg_data['config']['request']['headers'] = {h['key']: h['value'] for h in
                                                            json.loads(project_config.headers) if
                                                            h['key'] != ''}

        pro_cfg_data['config']['variables'] = json.loads(project_config.variables)
        return pro_cfg_data

    @staticmethod
    def merge_config(pro_config, scene_config):
        for _s in scene_config:
            for _p in pro_config['config']['variables']:
                if _p['key'] == _s['key']:
                    break
            else:
                pro_config['config']['variables'].append(_s)
        pro_config['config']['variables'] = [{v['key']: v['value']} for v in pro_config['config']['variables']
                                             if v['key'] != '']
        return pro_config

    def get_case(self, case, pro_config):
        if self.run_type:
            one_case = ApiMsg.query.filter_by(id=case.apiMsg_id).first()
        else:
            one_case = case

        temp_case_data = {'name': case.name,
                          'request': {'method': one_case.method, 'files': {}}}
        if case.up_func:
            temp_case_data['setup_hooks'] = [case.up_func]
        if case.down_func:
            temp_case_data['teardown_hooks'] = [case.down_func]
        if json.loads(one_case.headers):
            temp_case_data['request']['headers'] = {h['key']: h['value'] for h in json.loads(one_case.headers)
                                                    if h['key']}

        if one_case.status_url == '0':
            temp_case_data['request']['url'] = pro_config.host + one_case.url
        elif one_case.status_url == '1':
            temp_case_data['request']['url'] = pro_config.host_two + one_case.url
        elif one_case.status_url == '2':
            temp_case_data['request']['url'] = pro_config.host_three + one_case.url
        elif one_case.status_url == '3':
            temp_case_data['request']['url'] = pro_config.host_four + one_case.url

        if one_case.func_address:
            temp_case_data['import_module_functions'] = [
                'func_list.{}'.format(one_case.func_address.replace('.py', ''))]
        # if self.run_type:
        if not self.run_type or json.loads(case.status_variables)[0]:
            if not self.run_type or json.loads(case.status_variables)[1]:
                if one_case.method == 'GET':
                    temp_case_data['request']['params'] = {variable['key']: variable['value'] for variable in
                                                           json.loads(case.variables) if variable['key']}
                else:
                    if one_case.variable_type == 'data':
                        temp_case_data['request']['data'] = {variable['key']: variable['value'] for variable in
                                                             json.loads(case.variables) if
                                                             variable['param_type'] == 'string' and variable[
                                                                 'key']}

                        for variable in json.loads(case.variables):
                            if variable['param_type'] == 'file':
                                temp_case_data['request']['files'].update({
                                    variable['key']: (
                                        variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                                        CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})
                    else:

                        temp_case_data['request']['json'] = json.loads(case.variables)
            else:
                if one_case.method == 'GET':
                    temp_case_data['request']['params'] = {variable['key']: variable['value'] for variable in
                                                           json.loads(one_case.variables) if variable['key']}
                else:
                    if one_case.variable_type == 'data':
                        temp_case_data['request']['data'] = {variable['key']: variable['value'] for variable in
                                                             json.loads(one_case.variables) if
                                                             variable['param_type'] == 'string' and variable[
                                                                 'key']}

                        for variable in json.loads(one_case.variables):
                            if variable['param_type'] == 'file':
                                temp_case_data['request']['files'].update({
                                    'file': (variable['value'].split('/')[-1], open(variable['value'], 'rb'),
                                             CONTENT_TYPE['.{}'.format(variable['value'].split('.')[-1])])})
                    else:

                        temp_case_data['request']['json'] = json.loads(one_case.variables)

        if not self.run_type or json.loads(case.status_extract)[0]:
            if not self.run_type or json.loads(case.status_extract)[1]:
                temp_case_data['extract'] = [{ext['key']: ext['value']} for ext in json.loads(case.extract) if
                                             ext['key']]
            else:
                if json.loads(one_case.extract):
                    temp_case_data['extract'] = [{ext['key']: ext['value']} for ext in
                                                 json.loads(one_case.extract) if ext['key']]

        if not self.run_type or json.loads(case.status_validate)[0]:
            if not self.run_type or json.loads(case.status_validate)[1]:
                temp_case_data['validate'] = [{val['comparator']: [val['key'], val['value']]} for val in
                                              json.loads(case.validate) if val['key']]
            else:
                if json.loads(one_case.validate):
                    temp_case_data['validate'] = [{val['comparator']: [val['key'], val['value']]} for val in
                                                  json.loads(one_case.validate) if val['key']]
        return temp_case_data

    def all_cases_data(self):
        temp_case = []
        if self.scene_names:
            scene_ids = [Scene.query.filter_by(name=n).first().id for n in self.scene_names]
            for scene in scene_ids:
                scene_data = Scene.query.filter_by(id=scene).first()
                pro_config = self.pro_config(scene_data.project_id)

                if scene_data.func_address:
                    pro_config['config']['import_module_functions'] = [
                        'func_list.{}'.format(scene_data.func_address.replace('.py', ''))]

                if scene_data.variables:
                    scene_config = json.loads(scene_data.variables)
                else:
                    scene_config = []
                pro_config = self.merge_config(pro_config, scene_config)

                for case in ApiCase.query.filter_by(scene_id=scene).order_by(ApiCase.num.asc()).all():
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

            if config_data.func_address:
                pro_config['config']['import_module_functions'] = [
                    'func_list.{}'.format(config_data.func_address.replace('.py', ''))]

            pro_config = self.merge_config(pro_config, _config)
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
        res['stat']['successes'] = "{} ({}%)".format(res['stat']['successes'],
                                                     int(res['stat']['successes'] / res['stat']['testsRun'] * 100))
        res['stat']['failures'] = "{} ({}%)".format(res['stat']['failures'],
                                                    int(res['stat']['failures'] / res['stat']['testsRun'] * 100))

        import collections
        tree = lambda: collections.defaultdict(tree)
        some_dict = tree()
        some_dict = some_dict.update(res)
        print(some_dict)
        for num, rec in enumerate(res['records']):
            # try:
            # if not rec['meta_data'].get('url'):
            #     rec['meta_data']['url'] = self.temporary_url[num] + '\n(url请求失败，这为原始url，)'
            if 'Linux' in platform.platform():
                rec['meta_data']['response_time(ms)'] = rec['meta_data'].get('response_time_ms')
            if rec['meta_data'].get('response_headers'):
                rec['meta_data']['response_headers'] = dict(res['records'][num]['meta_data']['response_headers'])
            if rec['meta_data'].get('request_headers'):
                rec['meta_data']['request_headers'] = dict(res['records'][num]['meta_data']['request_headers'])

            if rec['meta_data'].get('request_body'):
                if isinstance(rec['meta_data']['request_body'], bytes):
                    if b'filename=' in rec['meta_data']['request_body']:
                        rec['meta_data']['request_body'] = '暂不支持显示文件上传的request_body'
                    else:
                        rec['meta_data']['request_body'] = rec['meta_data']['request_body'].decode('unicode-escape')
                        # rec['meta_data']['request_body'] = bytes.decode(rec['meta_data']['request_body'])
            if rec['meta_data'].get('response_body'):
                if isinstance(rec['meta_data']['response_body'], bytes):
                    rec['meta_data']['response_body'] = bytes.decode(rec['meta_data']['response_body'])
                    # except Exception as e:
                    #     print(e)
            if not rec['meta_data'].get('response_headers'):
                rec['meta_data']['response_headers'] = 'None'

        res['time']['start_at'] = now_time.strftime('%Y/%m/%d %H:%M:%S')
        jump_res = json.dumps(res, ensure_ascii=False)
        if self.run_type:
            self.new_report_id = Report.query.filter_by(
                data='{}.txt'.format(now_time.strftime('%Y/%m/%d %H:%M:%S'))).first().id
            with open('{}{}.txt'.format(REPORT_ADDRESS, self.new_report_id), 'w') as f:
                f.write(jump_res)
        return jump_res
