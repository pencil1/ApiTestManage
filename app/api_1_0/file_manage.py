from flask import jsonify, request
from . import api
from ..util.global_variable import *


# 上传文件
@api.route('/upload', methods=['POST'], strict_slashes=False)
def api_upload():
    data = request.files
    # try:
    file = data['file']
    skip = request.form.get('skip')
    # print(request.form)
    if os.path.exists(os.path.join(FILE_ADDRESS, file.filename)) and not skip:
        return jsonify({"msg": "文件已存在，请修改文件名字后再上传", "status": 0})

    else:
        file.save(os.path.join(FILE_ADDRESS, file.filename))
        return jsonify({'data': os.path.join(FILE_ADDRESS, file.filename), "msg": "上传成功", "status": 1})

    # except Exception as e:
    #     print(e)
    #     return jsonify({'data': '', "msg": "上传失败，请联系管理员或者换文件重试", "status": 0})


@api.route('/checkFile', methods=['POST'], strict_slashes=False)
def check_file():
    data = request.json

    address = data.get('address')
    if os.path.exists(address):
        return jsonify({"msg": "文件已存在", "status": 0})
    else:
        return jsonify({"msg": "文件不存在", "status": 1})