from flask import jsonify, request
from . import api
from ..util.global_variable import *


# 上传文件
@api.route('/upload', methods=['POST'], strict_slashes=False)
def api_upload():
    data = request.files
    # try:
    file = data['file']
    if os.path.exists(os.path.join(FILE_ADDRESS, file.filename)):
        return jsonify({"msg": "文件已存在，请修改文件名字后再上传", "status": 0})
    file.save(os.path.join(FILE_ADDRESS, file.filename))

    return jsonify({'data': os.path.join(FILE_ADDRESS, file.filename), "msg": "上传成功", "status": 1})

    # except Exception as e:
    #     print(e)
    #     return jsonify({'data': '', "msg": "上传失败，请联系管理员或者换文件重试", "status": 0})
