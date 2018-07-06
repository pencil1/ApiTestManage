from flask import Blueprint

api = Blueprint('api', __name__)

from . import case_manage, model_manage, project_manage, report_manage, build_in_manage, scene_manage, login, \
    test_tool, task_manage, file_manage, sceneConfig#, errors
