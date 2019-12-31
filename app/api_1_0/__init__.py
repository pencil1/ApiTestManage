from flask import Blueprint, current_app, request
from ..util.custom_decorator import login_required
import copy
import json

api = Blueprint('api', __name__)

from . import api_msg_manage, module_manage, project_manage, report_manage, build_in_manage, case_manage, login, \
    test_tool, task_manage, file_manage, config, case_set_manage, test_case_file_manage, errors


@api.before_request
def before_request():
    try:
        current_app.logger.info('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, request.json))
    except Exception as e:
        print(e)
    # print(request.remote_addr)


@api.after_request
def after_request(r):
    if 'downloadFile' in request.url:
        return r
    result = copy.copy(r.response)
    if isinstance(result[0], bytes):
        result[0] = bytes.decode(result[0])
    if 'apiMsg/run' not in request.url and 'report/run' not in request.url and 'report/list' not in request.url:
        current_app.logger.info('url:{} ,method:{},返回数据:{}'.format(request.url, request.method, json.loads(result[0])))
    return r
