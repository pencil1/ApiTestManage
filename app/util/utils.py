# encoding: utf-8
import ast
import importlib
import json
import re
import types
from copy import deepcopy
from .httprunner.parser import variable_regexp, function_regexp, function_regexp_compile


# 全角转成半角
def full_to_half(s):
    if s is None:
        return s
    n = ''
    for char in s:
        num = ord(char)
        if num == 0x3000:  # 将全角空格转成半角空格
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:  # 将其余全角字符转成半角字符
            num -= 0xFEE0
        num = chr(num)
        n += num
    return n


# 半角转成全角
def half_to_full(s):
    if s is None:
        return s
    n = ''
    for char in s:
        num = ord(char)
        if (num == 32):  # 半角空格转成全角
            num = 0x3000
        elif 33 <= num <= 126:
            num += 65248  # 16进制为0xFEE0
        num = chr(num)
        n += num
    return n


def auto_num(num, model, **kwargs):
    """自动返回编号的最大值"""
    if not num:
        if not model.query.filter_by(**kwargs).all():
            return 1
        else:
            return model.query.filter_by(**kwargs).order_by(model.num.desc()).first().num + 1
    return num


def num_sort(new_num, old_num, list_data, old_data):
    """修改排序,自动按新旧序号重新排列"""
    if old_data not in list_data:
        old_data.num = len(list_data) + 1
    else:
        _temp_data = list_data.pop(list_data.index(old_data))
        list_data.insert(new_num - 1, _temp_data)
        if old_num == new_num:
            pass
        elif old_num > new_num:
            for n, m in enumerate(list_data[new_num - 1:old_num + 1]):
                m.num = new_num + n

        elif old_data.num < new_num:
            for n, m in enumerate(list_data[old_num - 1:new_num + 1]):
                m.num = old_num + n


# variable_regexp = r"\$([\w_]+)"
# function_regexp = r"\$\{([\w_]+\([\$\w\.\-_ =,]*\))\}"
# function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\.\-/_ =,]*)\)$")
# function_regexp_compile = re.compile(r"^([\w_]+)\(([\$\w\W\.\-/_ =,]*)\)$")
def tree_change(change_data):
    """递归遍历change_data，返回树状结构数据"""
    result = []
    for _data in change_data:
        if _data['higher_id'] == 0:
            result.append(_data)
        else:
            def traverse_children(children_data):
                for _c in children_data:

                    if _c['id'] == _data['higher_id'] and _c['project_id'] == _data['project_id']:
                        if not _c.get('children'):
                            _c['children'] = []
                        _c['children'].append(_data)
                        break
                    else:
                        if _c.get('children'):
                            traverse_children(_c['children'])

            traverse_children(result)
    return result


def extract_variables(content):
    """ extract all variable names from content, which is in format $variable
    @param (str) content
    @return (list) variable name list

    e.g. $variable => ["variable"]
         /blog/$postid => ["postid"]
         /$var1/$var2 => ["var1", "var2"]
         abc => []
    """
    try:
        return re.findall(variable_regexp, content)
    except TypeError:
        return []


def extract_functions(content):
    """ extract all functions from string content, which are in format ${fun()}
    @param (str) content
    @return (list) functions list

    e.g. ${func(5)} => ["func(5)"]
         ${func(a=1, b=2)} => ["func(a=1, b=2)"]
         /api_1_0/1000?_t=${get_timestamp()} => ["get_timestamp()"]
         /api_1_0/${add(1, 2)} => ["add(1, 2)"]
         "/api_1_0/${add(1, 2)}?_t=${get_timestamp()}" => ["add(1, 2)", "get_timestamp()"]
    """
    try:
        return re.findall(function_regexp, content)
    except TypeError:
        return []


def check_case(case_data, func_address):
    module_functions_dict = {}
    if func_address:
        for f in json.loads(func_address):
            import_path = 'func_list.{}'.format(f.replace('.py', ''))
            func_list = importlib.reload(importlib.import_module(import_path))
            module_functions_dict.update({name: item for name, item in vars(func_list).items() if
                                          isinstance(item, types.FunctionType)})
            # module_functions_dict = dict(filter(is_function, vars(func_list).items()))

    if isinstance(case_data, list):
        for c in case_data:
            json_c = json.dumps(c)
            num = json_c.count('$')
            variable_num = len(extract_variables(json_c))
            func_num = len(extract_functions(json_c))
            if not c['case_name']:
                return '存在没有命名的用例，请检查'
            if num != (variable_num + func_num):
                return '‘{}’用例存在格式错误的引用参数或函数'.format(c['case_name'])
            if func_address:
                for func in extract_functions(json_c):
                    func = func.split('(')[0]
                    if func not in module_functions_dict:
                        return '{}用例中的函数“{}”在文件引用中没有定义'.format(c['case_name'], func)

    else:
        num = case_data.count('$')
        variable_num = len(extract_variables(case_data))
        func_num = len(extract_functions(case_data))
        if num != (variable_num + func_num):
            return '‘业务变量’存在格式错误的引用参数或函数'
        if func_address:
            for func in extract_functions(case_data):
                func = func.split('(')[0]
                if func not in module_functions_dict:
                    return '函数“{}”在文件引用中没有定义'.format(func)


def convert(variable):
    """ 同层次参数中，存在引用关系就先赋值
    eg:
        phone:123
        name:$phone
        => phone:123
           name:123
    """
    _temp = json.dumps(variable)
    content = {v['key']: v['value'] for v in variable if v['key'] != ''}
    for variable_name in extract_variables(_temp):
        if content.get(variable_name):
            # content contains one or several variables
            _temp = _temp.replace(
                "${}".format(variable_name),
                str(content.get(variable_name)), 1
            )
            content = {v['key']: v['value'] for v in json.loads(_temp) if v['key'] != ''}

    return _temp


def change_cron(expression):
    args = {}
    expression = expression.split(' ')
    if expression[0] != '?':
        args['second'] = expression[0]
    if expression[1] != '?':
        args['minute'] = expression[1]
    if expression[2] != '?':
        args['hour'] = expression[2]
    if expression[3] != '?':
        args['day'] = expression[3]
    if expression[4] != '?':
        args['month'] = expression[4]
    if expression[5] != '?':
        args['day_of_week'] = expression[5]
    return args


def parse_string_value(str_value):
    """ parse string to number if possible
    e.g. "123" => 123
         "12.2" => 12.3
         "abc" => "abc"
         "$var" => "$var"
    """
    try:
        return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        # e.g. $var, ${func}
        return str_value


def parse_function(content):
    """ parse function name and args from string content.

    Args:
        content (str): string content

    Returns:
        dict: function meta dict

            {
                "func_name": "xxx",
                "args": [],
                "kwargs": {}
            }

    Examples:
        >>> parse_function("func()")
        {'func_name': 'func', 'args': [], 'kwargs': {}}

        >>> parse_function("func(5)")
        {'func_name': 'func', 'args': [5], 'kwargs': {}}

        >>> parse_function("func(1, 2)")
        {'func_name': 'func', 'args': [1, 2], 'kwargs': {}}

        >>> parse_function("func(a=1, b=2)")
        {'func_name': 'func', 'args': [], 'kwargs': {'a': 1, 'b': 2}}

        >>> parse_function("func(1, 2, a=3, b=4)")
        {'func_name': 'func', 'args': [1, 2], 'kwargs': {'a':3, 'b':4}}

    """
    matched = function_regexp_compile.match(content)
    function_meta = {
        "func_name": matched.group(1),
        "args": [],
        "kwargs": {}
    }

    args_str = matched.group(2).strip()
    if args_str == "":
        return function_meta

    args_list = args_str.split(',')
    for arg in args_list:
        arg = arg.strip()
        if '=' in arg:
            key, value = arg.split('=')
            function_meta["kwargs"][key.strip()] = parse_string_value(value.strip())
        else:
            function_meta["args"].append(parse_string_value(arg))

    return function_meta


def try_switch_data(d):
    try:
        return ast.literal_eval(d)
    except:
        return d


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
        # print(f.read())
        # print(f.read().replace('null', '""'))
        content_json = json.loads(f.read().replace('null', '""'))
    api_list = []
    for k, v in content_json['paths'].items():

        def get_param(schema, request_type, swagger=False):
            """
            Args:
                schema:
                request_type:
                swagger: 是否生成swagger格式备注数据流
            Returns:

            """
            if request_type == 'json':
                if schema.get('type') == 'array':
                    _list_d = [{}]

                    if not schema['items'].get('$ref'):
                        return []
                    # print(schema)
                    # print(1111)
                    # print(schema['items'])
                    for _k2, _v1 in content_json['definitions'][schema['items']['$ref'].split('/')[-1]][
                        'properties'].items():
                        if _v1.get('$ref'):
                            _list_d[0][_k2] = get_param(_v1, request_type, swagger)
                        elif _v1.get('type') == 'array':
                            _list_d[0][_k2] = get_param(_v1, request_type, swagger)
                        else:
                            if swagger:
                                if _v1.get('description'):
                                    _v1['remark'] = _v1.pop('description')
                                _list_d[0][_k2] = _v1
                            else:
                                _list_d[0][_k2] = ''
                    return _list_d
                else:
                    _dict = {}
                    if not schema.get('$ref'):
                        return {}

                    for _k, _v in content_json['definitions'][schema['$ref'].split('/')[-1]]['properties'].items():
                        if _v.get('$ref'):
                            _dict[_k] = get_param(_v, request_type, swagger)
                        elif _v.get('type') == 'array':
                            _dict[_k] = get_param(_v, request_type, swagger)
                        else:
                            if swagger:
                                if _v.get('description'):
                                    _v['remark'] = _v.pop('description')
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

        # if 'assetLeaseSign/getCurNode' not in k:
        #     continue

        # print(v)
        for k1, v1 in v.items():
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
            _temp_data['url'] = content_json.get('basePath') + k if content_json.get('basePath') else k
            _temp_data['method'] = k1.upper()
            _temp_data['name'] = v1.get('summary')
            # print(_temp_data['name'])
            # if _temp_data['name'] != '获取换电站型号详情':
            #     continue
            # print(_temp_data)
            # print(k1)
            # if k1 != 'get':
            if 'application/json' in json.dumps(v1.get('consumes')):
                _temp_data['variable_type'] = 'json'
            else:
                _temp_data['variable_type'] = 'data'
            if v1.get('parameters'):
                for v3 in v1.get('parameters'):
                    if v3.get('in') == 'query':
                        _temp_data['variable'].append(
                            {'key': v3.get('name'), 'value': '', 'remark': v3.get('description'),
                             'param_type': 'string'})
                    if v3.get('in') == 'body':
                        if _temp_data['variable_type'] == 'json':
                            _temp_data['json_variable'] = get_param(v3['schema'], _temp_data['variable_type'])
                            _temp_data['swagger_json_variable'] = get_param(v3['schema'], _temp_data['variable_type'],
                                                                            swagger=True)
                            # print(_temp_data['swagger_json_variable'])
                            # print(11111)
                        else:
                            _temp_data['variable'].append(get_param(v3['schema'], _temp_data['variable_type']))
            # print(_temp_data)
            api_list.append(deepcopy(_temp_data))
    return api_list


def is_chinese(string):
    """
    检查整个字符串是否包含中文
    :param string: 需要检查的字符串
    :return: bool
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True

    return False


if __name__ == '__main__':
    a = swagger_change('/Users/zw/Documents/auto/files/基础信息管理服务_OpenAPI.json')
    print(a)
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
