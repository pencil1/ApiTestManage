from flask import Blueprint, current_app, request
# from flask_login import current_user

from ..models import Logs, db
from ..util.custom_decorator import login_required
import copy, yaml, os
import json

api = Blueprint('api', __name__)

with open(r'{}/app/pom.yaml'.format(os.path.abspath('.')), 'r', encoding='utf-8') as f:
    sso_config = yaml.load(f.read(), Loader=yaml.FullLoader)

from . import api_msg_manage, api_set_manage, project_manage, report_manage, build_in_manage, case_manage, login, \
    test_tool, task_manage, file_manage, config, case_set_manage, errors



@api.before_request
def before_request():
    try:
        # print('url:{} ,method:{},请求参数:{}'.format(request.url, request.method, request.json))
        current_app.logger.info(
            'ip:{}, url:{} ,method:{},请求参数:{}'.format(request.headers.get('X-Forwarded-For'), request.url,
                                                      request.method, request.json))
    except Exception as e:
        pass
    # print(request.remote_addr)


@api.after_request
def after_request(r):
    uid = request.headers.get('userId')
    # uid = current_user.id if getattr(current_user, 'id', None) else None
    new_project = Logs(ip=request.headers.get('X-Forwarded-For'),
                       uid=uid,
                       url=request.url,
                       log_type=1)
    db.session.add(new_project)
    db.session.commit()
    if 'downloadFile' in request.url:
        return r
    result = copy.copy(r.response)
    if isinstance(result[0], bytes):
        result[0] = bytes.decode(result[0])
    if 'apiMsg/run' not in request.url and 'report/run' not in request.url and 'report/list' not in request.url and not isinstance(
            result[0], str):
        current_app.logger.info('url:{} ,method:{},返回数据:{}'.format(request.url, request.method, json.loads(result[0])))
    return r
