import random
import datetime
import json
from copy import deepcopy
# from case_gener import Util

def identity_generator():
    # 身份证号的前两位，省份代号
    sheng = (
        '11', '12', '13', '14', '15', '21', '22', '23', '31', '32', '33', '34', '35', '36', '37', '41', '42', '43',
        '44',
        '45', '46', '50', '51', '52', '53', '54', '61', '62', '63', '64', '65', '66')

    # 随机选择距离今天在7000到25000的日期作为出生日期（没有特殊要求我就随便设置的，有特殊要求的此处可以完善下）
    birthdate = (datetime.date.today() - datetime.timedelta(days=random.randint(8000, 15000)))

    # 拼接出身份证号的前17位（第3-第6位为市和区的代码，中国太大此处就偷懒了写了定值，有要求的可以做个随机来完善下；第15-第17位为出生的顺序码，随机在100到199中选择）
    ident = sheng[random.randint(0, 31)] + '0101' + birthdate.strftime("%Y%m%d") + str(random.randint(100, 199))
    # ident = '44180219921012383'
    # 前17位每位需要乘上的系数，用字典表示，比如第一位需要乘上7，最后一位需要乘上2
    coe = {1: 7, 2: 9, 3: 10, 4: 5, 5: 8, 6: 4, 7: 2, 8: 1, 9: 6, 10: 3, 11: 7, 12: 9, 13: 10, 14: 5, 15: 8, 16: 4,
           17: 2}
    summation = 0

    # for循环计算前17位每位乘上系数之后的和
    for i in range(17):
        summation = summation + int(ident[i:i + 1]) * coe[i + 1]  # ident[i:i+1]使用的是python的切片获得每位数字

    # 前17位每位乘上系数之后的和除以11得到的余数对照表，比如余数是0，那第18位就是1
    key = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}

    # 拼接得到完整的18位身份证号
    return ident + key[summation % 11]


class TraverseDict(object):
    def __init__(self):
        self.d_list = []

    def get_dict_keys_path(self, result, path=None):
        """  遍历dict，返回字典的值的路径和值组成的list

        :param result: 字典
        :param path: 递归使用，部分路径的值
        """
        for k, v in result.items():
            if isinstance(v, list) and v:  # and v  主要是v有可能为空list
                for num, a1 in enumerate(v):
                    if path:
                        self.get_dict_keys_path(a1, "{},{},{}".format(path, k, num))
                    else:
                        self.get_dict_keys_path(a1, "{},{}".format(k, num))
            elif isinstance(v, dict) and v:  # and v  主要是v有可能为dict
                if path:
                    self.get_dict_keys_path(v, "{},{}".format(path, k, ))
                else:
                    self.get_dict_keys_path(v, k)
            else:
                if path:
                    if not v:  # 当v为Fasle时，把它赋值None，已方便删除该key
                        v = None
                    _t = "{},{},{}".format(path, k, v)
                    t2 = _t.split(',')
                    for n, value in enumerate(t2):  # 遍历t2,转换里面为存数字的str为int
                        try:
                            t2[n] = int(value)
                        except:
                            pass
                    self.d_list.append(t2)
                else:
                    self.d_list.append([k, v])

    def del_key(self, result, path_list):
        """  根据路径删除字典中指定的值

        :param result: dict
        :param path_list: 某个指定的值的路径list
        """
        num = len(path_list)
        if num == 1:
            return result.pop(path_list[0])

        return self.del_key(result[path_list.pop(0)], path_list)

    def data_tidy(self, result):
        """  删除指定规则中字典的值

        """
        for path in self.d_list:
            if path[-1] == 'None':
                self.del_key(result, path[:-1])
            elif path[-2].find('id') != -1 or path[-2].find('Id') != -1 or path[-2].find('Time') != -1:
                self.del_key(result, path[:-1])
            elif path[0].find('request') != -1:
                self.del_key(result, path[:-1])
        self.d_list.clear()  # 清理list，防止下次使用时保留上次的数据引起报错

def encode_object(obj):
    """ json.dumps转化时，先把属于bytes类型的解码，若解码失败返回str类型，和其他对象属性统一转化成str"""
    if isinstance(obj, bytes):
        try:
            return bytes.decode(obj)
        except Exception as e:
            return str(obj)
    else:
        return str(obj)


def swagger_change(file_path):
    with open(file_path, "r+", encoding="utf-8-sig") as f:
        content_json = json.loads(f.read())
    api_list = []
    for k, v in content_json['paths'].items():
        _temp_data = {
            'name': '',
            'desc': '',
            'url': '',
            'status_url': '0',
            'skip': '',
            # 'apiMsgId': '',
            # 'gather_id': '',
            'variable_type': '',
            'variable': [],
            'json_variable': '',
            'swagger_json_variable': '',
            'extract': [],
            'validate': [],
            'param': [],
            'method': 'POST',
            'header': [],
        }

        def get_param(schema, request_type, swagger=False):
            if request_type == 'json':
                if schema.get('type') == 'array':
                    _list_d = [{}]
                    for _k2, _v1 in content_json['definitions'][schema['items']['$ref'].split('/')[-1]][
                        'properties'].items():
                        if _v1.get('$ref'):
                            _list_d[0][_k2] = get_param(_v1, request_type,swagger)
                        elif _v1.get('type') == 'array':
                            _list_d[0][_k2] = get_param(_v1, request_type,swagger)
                        else:
                            if swagger:
                                if _v1.get('description'):
                                    _v1['remark'] = _v1.pop('description')
                                    # _v1['remark'] = _v1.get('description')
                                _list_d[0][_k2] = _v1
                            else:
                                _list_d[0][_k2] = ''
                    return _list_d
                else:
                    _dict = {}
                    for _k, _v in content_json['definitions'][schema['$ref'].split('/')[-1]]['properties'].items():
                        if _v.get('$ref'):
                            _dict[_k] = get_param(_v, request_type,swagger)
                        elif _v.get('type') == 'array':
                            _dict[_k] = get_param(_v, request_type,swagger)
                        else:
                            if swagger:
                                if _v.get('description'):
                                    _v['remark'] = _v.pop('description')
                                    # _v['remark'] = _v.get('description')
                                    # del _v['description']
                                _dict[_k] = _v
                            else:
                                _dict[_k] = ''
                    return _dict
            else:
                _list = []
                if schema.get('type') == 'array':
                    _list_d = []
                    r = content_json['definitions'][schema['items']['$ref'].split('/')[-1]]['properties'].items()
                else:
                    ref = schema['$ref'].split('/')[-1]
                    for _key, _value in content_json['definitions'][ref]['properties'].items():
                        _d = {'value': '', 'param_type': 'string', 'remark': _value['description'], 'key': _key}
                        _d.update(_value)
                        _list.append(_d)
                        # if k.get('$ref'):
                        #     pass

        _temp_data['url'] = k
        if not 'addLeaseSignSummary' in k:
            continue

        for k1, v1 in v.items():
            _temp_data['method'] = k1.upper()
            _temp_data['name'] = v1.get('summary')
            # print(k1)
            # if k1 != 'get':
            if 'application/json' in json.dumps(v1.get('consumes')):
                _temp_data['variable_type'] = 'json'
                # else:
                #     _temp_data['variableType'] = 'data'
                # print()
                # print(v1['consumes'])
            if v1.get('parameters'):
                for v3 in v1.get('parameters'):
                    if v3.get('in') == 'query':
                        _temp_data['param'].append(
                            {'key': v3.get('name'), 'value': '', 'remark': v3.get('description')})
                    if v3.get('in') == 'body':
                        if _temp_data['variable_type'] == 'json':
                            # _temp_data['json_variable'] = get_param(v3['schema'], _temp_data['variable_type'])
                            _temp_data['swagger_json_variable'] = get_param(v3['schema'], _temp_data['variable_type'],
                                                                            swagger=True)
                            # print(_temp_data['swagger_json_variable'])
                            # print(11111)
                        else:
                            _temp_data['variable'].append(get_param(v3['schema'], _temp_data['variable_type']))
        api_list.append(deepcopy(_temp_data))
    return api_list

if __name__ == '__main__':

    a = swagger_change('/Users/zw/Documents/auto/files/123.json')
    print(a)
    # for a1 in a:
    #     if 'addLeaseSignSummary' in a1['url']:
    #         Util().gen_cases(a1)
    # for a1 in a:
    #     if '/addLocationConstruction' in a1['url']:
    #         print(a1['swagger_json_variable'])
    # func_list = importlib.reload(importlib.import_module(r"func_list.abuild_in_fun.py"))
    # module_functions_dict = {name: item for name, item in vars(func_list).items() if
    #                          isinstance(item, types.FunctionType)}
    # print(module_functions_dict)
    # a = '${func({"birthday": "199-02-02"; "expire_age": "65周岁"; "sex": "2"},123,3245)}'
    # b = '${func([123],123)}'
    # print(extract_functions(a))
    # matched = parse_function(extract_functions(b)[0])
    #
    # print(matched)
