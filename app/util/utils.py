# encoding: utf-8
import importlib
import json
import re
import types


def auto_num(num, model, **kwargs):
    """
    自动返回编号的最大值
    :param num:
    :param model:
    :param kwargs:
    :return:
    """
    if not num:
        if not model.query.filter_by(**kwargs).all():
            return 1
        else:
            return model.query.filter_by(**kwargs).order_by(model.num.desc()).first().num + 1
    return num


def num_sort(new_num, old_num, model, **kwargs):
    """
    修改排序功能
    :param new_num:
    :param old_num:
    :param model:
    :param kwargs:
    :return:
    """
    if int(new_num) < old_num:  # 当需要修改的序号少于原来的序号
        model.query.filter_by(num=old_num, **kwargs).first().num = 99999
        for n in reversed(range(int(new_num), old_num)):
            change_num = model.query.filter_by(num=n, **kwargs).first()
            if change_num:
                change_num.num = n + 1
        model.query.filter_by(num=99999, **kwargs).first().num = new_num

    else:  # 当需要修改的序号大于原来的序号
        model.query.filter_by(num=old_num, **kwargs).first().num = 99999
        for n in range(old_num + 1, int(new_num) + 1):
            change_num = model.query.filter_by(num=n, **kwargs).first()
            if change_num:
                change_num.num = n - 1
        model.query.filter_by(num=99999, **kwargs).first().num = new_num


variable_regexp = r"\$([\w_]+)"
function_regexp = r"\$\{([\w_]+\([\$\w\.\-_ =,]*\))\}"


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
         /api/1000?_t=${get_timestamp()} => ["get_timestamp()"]
         /api/${add(1, 2)} => ["add(1, 2)"]
         "/api/${add(1, 2)}?_t=${get_timestamp()}" => ["add(1, 2)", "get_timestamp()"]
    """
    try:
        return re.findall(function_regexp, content)
    except TypeError:
        return []


def check_case(case_data, func_address):
    if func_address:
        import_path = 'func_list.{}'.format(func_address.replace('.py', ''))
        func_list = importlib.reload(importlib.import_module(import_path))
        module_functions_dict = {name: item for name, item in vars(func_list).items() if
                                 isinstance(item, types.FunctionType)}
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
    _temp = json.dumps(variable)
    content = {v['key']: v['value'] for v in variable if v['key'] != ''}
    for variable_name in extract_variables(_temp):
        if content.get(variable_name):
            # content contains one or several variables
            _temp = _temp.replace(
                "${}".format(variable_name),
                str(content.get(variable_name)), 1
            )
    return _temp


def merge_config(pro_config, scene_config):
    """
    合并公用项目配置和业务集合配置
    :param pro_config:
    :param scene_config:
    :return:
    """
    for _s in scene_config:
        for _p in pro_config['config']['variables']:
            if _p['key'] == _s['key']:
                break
        else:
            pro_config['config']['variables'].append(_s)

    _temp = convert(pro_config['config']['variables'])
    pro_config['config']['variables'] = [{v['key']: v['value']} for v in json.loads(_temp)
                                         if v['key']]
    # pro_config['config']['output'] = ['token']
    return pro_config


if __name__ == '__main__':
    a = '${func($test)},$open,'
    print(extract_variables(a))
