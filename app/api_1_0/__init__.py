from flask import Blueprint


api = Blueprint('api', __name__)

from . import api_msg_manage, module_manage, project_manage, report_manage, build_in_manage, case_manage, login, \
    test_tool, task_manage, file_manage, config, suite_manage, case_set_manage, errors



# if 'Linux' in platform.platform():
#     from . import errors
