from flask import jsonify, current_app
from . import api


@api.app_errorhandler(Exception)
def page_not_found(e):
    current_app.logger.exception(e)
    # response = jsonify({'error': 'not found','data':e})
    # response.status_code = 404
    return jsonify({'msg': '服务器异常，请联系管理员', 'status': 0, 'error': '{}'.format(e)})
