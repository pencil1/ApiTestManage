from flask import jsonify, current_app, request
from . import api
import traceback
from ..util.error_code import *


@api.app_errorhandler(404)
def page_not_found(e):
    current_app.logger.exception('后台不存在此请求url:{}'.format(request.url))
    return jsonify({'msg': '后台不存在此请求'})


@api.app_errorhandler(ParameterException)
def error_handler(e):
    current_app.logger.exception(traceback.format_exc())
    return jsonify({'msg': e.msg, 'status': e.status})

@api.app_errorhandler(ServerError)
def error_handler(e):
    current_app.logger.exception(traceback.format_exc())
    return jsonify({'msg': e.msg, 'status': e.status})


@api.app_errorhandler(SwaggerParseError)
def error_handler(e):
    current_app.logger.exception(traceback.format_exc())
    return jsonify({'msg': e.msg, 'status': e.status})


@api.app_errorhandler(Exception)
def error_handler(e):
    current_app.logger.exception(traceback.format_exc())
    # print(e.msg)
    # print(e.status)
    # return jsonify(e)
    return jsonify({'msg': '服务器异常，请查看返回的error信息，无法处理则联系管理员', 'status': 0, 'error': '{}'.format(traceback.format_exc())})
