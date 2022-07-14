import copy
import re
import json
from collections import OrderedDict
from allpairspy import AllPairs
from jinja2 import Template
from app.util.error_code import SwaggerParseError
from ..util import utils
# from .faker import fakerist
# from flask import current_app

# TODO 接口入参可能是list，但也可能是数组。比如建站管理的新增租赁用印信息列表
# TODO 未处理 1 和 '1' 的区别

class CaseMaker:
    # 备用方案
    def __iter_x(self, x):
        if isinstance(x, dict):
            for key, value in x.items():
                yield (key, value)
        elif isinstance(x, list):
            for index, value in enumerate(x):
                yield (index, value)

    # 用来处理嵌套数组和列表
    def __flat(self, x):
        for key, value in self.__iter_x(x):
            if isinstance(value, (dict, list)):
                for k, v in self.__flat(value):
                    k = f'{key}_{k}'
                    yield (k, v)
            else:
                yield (key, value)

    # 全角转成半角
    def full_to_half(self, s):
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
    def half_to_full(self, s):
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

    # 去除左右空格+全角转半角
    def __format(self, data):
        # tmp = data.replace(" ", "")
        tmp2 = self.full_to_half(data.strip())
        return tmp2

    # 判断 remark 字符串是否需要 split 生成多条用例
    def is_multi_remark(self, f_remark):
        return True if f_remark.count(':') > 1 else False

    # 第0步，建模,将每个value重新赋值为{{key}}
    # TODO-A
    #   因为其他key名比如format和remark不是所有字段都提供，所以目前只是通过字典value中是否包含'type'这个key名来判断是否终端节点。
    #   如果字段中如果不含type字段，当前无法判断是终端节点还是普通节点。
    def make_model(self, data):
        if len(data) == 0:
            raise SwaggerParseError(msg="数据为空")
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    # 当前key判断为字段
                    if "type" in v:
                        data[k] = "{{" + k + "}}"
                    # 当前key判断为非字段，或者是字段不含type的非法场景
                    else:
                        self.make_model(data[k])
                elif isinstance(v, list):
                    v_count = len(v)
                    if v_count == 0:
                        raise SwaggerParseError(msg="数组为空异常")
                    # 兼容value中有数组的场景
                    for i in range(v_count):
                        self.make_model(v[i])
                elif not isinstance(v, (dict, list)):
                    # TODO-A
                    # raise SwaggerParseError(msg="openapi文档解析异常。存在不含type字段的非法终端节点，无法正常解析")
                    # print(f"{k}#{v}")
                    pass
                else:
                    raise SwaggerParseError(msg='建模获取value类型时异常')
        elif isinstance(data, list):
            data_len = len(data)
            if data_len == 0:
                raise SwaggerParseError(msg="数组为空异常")
            for j in range(data_len):
                self.make_model(data[j])
        else:
            raise SwaggerParseError(msg="接口详情解析异常")

        str_data = json.dumps(data, ensure_ascii=False)
        return str_data

    # 第6步 赋值
    # 调用render，将模组key列表和数据集value字典数组合并注意下是否能对 数组和字典各种嵌套的场景下能否填充
    # TODO 未调试
    def eval_model(self, data, expect_value):
        temp = Template(data)
        b = temp.render(expect_value)
        return b

'''
简单用例生成器：
统一用faker，边解析边赋值，生成单条用例
'''
class SimpleCaseMaker(CaseMaker):
    # 第0步，建模,将每个value重新赋值为{{key}}
    # TODO-A
    #   因为其他key名比如format和remark不是所有字段都提供，所以目前只是通过字典value中是否包含'type'这个key名来判断是否终端节点。
    #   如果字段中如果不含type字段，当前无法判断是终端节点还是普通节点。
    def make_model(self, data):
        if len(data) == 0:
            raise SwaggerParseError(msg='数据为空')
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    # 当前key判断为字段
                    vkeys = v.keys()
                    if "type" in v:
                        if v["type"] == 'integer':
                            data[k] = 233
                        elif v["type"] == "string":
                            if "format" in v:
                                if v['format'] == 'date-time':
                                    # data[k] = str(fakerist.future_datetime())
                                    data[k] = "2021-02-02"
                                else:
                                    data[k] = "default_string"
                            else:
                                data[k] = "default_string"
                        else:
                            data[k] = "default_type"
                    # 当前key判断为非字段，或者是字段不含type的非法场景
                    else:
                        self.make_model(data[k])
                elif isinstance(v, list):
                    v_count = len(v)
                    if v_count == 0:
                        raise SwaggerParseError(msg="数组为空异常")
                    # 兼容value中有数组的场景
                    for i in range(v_count):
                        self.make_model(v[i])
                elif not isinstance(v, (dict, list)):
                    # TODO-A
                    # raise SwaggerParseError(msg="openapi文档解析异常。存在不含type字段的非法终端节点，无法正常解析")
                    # print(f"{k}#{v}")
                    pass
                else:
                    raise SwaggerParseError(msg='建模获取value类型时异常')
        elif isinstance(data, list):
            data_len = len(data)
            if data_len == 0:
                raise SwaggerParseError(msg="数组为空异常")
            for j in range(data_len):
                self.make_model(data[j])
        else:
            raise SwaggerParseError(msg="接口详情解析异常")
        return data

    def gen_cases(self, api_data):

        # 解析接口相关信息
        api_method = api_data.get('method').lower()
        api_type = api_data.get('variableType')
        api_json = api_data.get('swagger_json_variable')
        api_data = api_data.get('json_variable')
        # api_param = api_data.get('param')
        api_data_json = copy.deepcopy(api_json)

        # print("\n 原始接口信息")
        # print(json.dumps(api_data_json, ensure_ascii=False))
        # if isinstance(api_data_json, dict):
        #     pass
        # elif isinstance(api_data_json, list):
        #     # TODO 一般不会有2层列表的场景，暂时固定取[0]
        #     # TODO 处理后要外面套一层[]
        #     api_data_json = api_data_json[0]
        #     print("暂未测试 openapi接口详情字段是列表的场景")
        # else:
        #     raise SwaggerParseError(msg="openapi接口详情字段格式异常")
        # final_cases = []

        # TODO 未测试
        if api_method == 'get':
            pass
            # # raise SwaggerParseError(msg="暂不支持get请求")
            # print("\n 原始接口信息")
            # print(json.dumps(api_param, ensure_ascii=False))
            # if isinstance(api_param, list):
            #     param_len = len(api_param)
            #     if param_len == 0:
            #         # restful风格，前端禁止生成用例操作
            #         pass
            #     else:
            #         # 非restful风格，
            #         for field in api_param:
            #             if 'key' in field.keys():
            #                 field['value'] = 111111
            #             else:
            #                 raise SwaggerParseError(msg='解析异常，get请求的param字段中不含key')
            # else:
            #     raise SwaggerParseError(msg='解析异常，get请求的param字段外层非列表')
            # return api_param

        # TODO
        elif api_method == 'post' and api_type == 'data':
            raise SwaggerParseError(msg="暂不支持post的form表单请求")
        elif api_method == 'post' and api_type == 'json':

            print("\n 原始接口信息")
            print(json.dumps(api_data_json, ensure_ascii=False))
            if isinstance(api_data_json, dict):
                pass
            elif isinstance(api_data_json, list):
                # TODO 一般不会有2层列表的场景，暂时固定取[0]
                # TODO 处理后要外面套一层[]
                api_data_json = api_data_json[0]
                print("暂未测试 openapi接口详情字段是列表的场景")
            else:
                raise SwaggerParseError(msg="openapi接口详情字段格式异常", status=0)

            final_cases = []
            # 接口字典数据建模并赋值
            final_case_dict = self.make_model(api_data_json)
            print(json.dumps(final_case_dict, ensure_ascii=False))
            final_cases.append(final_case_dict)

            return final_cases

        else:
            raise SwaggerParseError(msg="content-type类型异常，必须是【json、data、param】其中3种")




'''
算法用例生成器：
fixed用faker，multi用pairwise
'''
# TODO
class PairwiseCaseMaker(CaseMaker):

    # 给 pairwise调用
    def __is_valid(self, row):
        field_cur_num = len(row)
        # TODO 这个值最好从内部计算
        field_max_num = 3
        # if field_cur_num >= field_max_num:
        #     # 一年级 不能匹配 10-13岁
        #     if "XXX" == row[0] and "中文" == row[1]:
        #         return False
        #     else:
        #         return True
        # else:
        #     return True
        return True

    def __change_date(self, m):
        key = '\"' + str(m.group(1)) + '\"'
        # value = '\"' + str(m.group(2)) + '\"'
        mg = m.group(2)
        value = ''
        if mg.count('\'') > 1:
            value = mg.replace('\'', '\"')
        return f"{key}: {value}"

    # 将返回的pairs对象转成字典格式，给 test_pairwise 调用
    def format_pair(self, tmp):
        text3 = str(tmp).lstrip('Pairs(').rstrip(')')
        regex_cp = re.compile('([\u4e00-\u9fa5A-Za-z0-9]+)=([\u4e00-\u9fa5A-Za-z0-9\'\s]+)')
        pairs = '{' + regex_cp.sub(self.__change_date, text3) + '}'
        pairs_json = json.loads(pairs)
        return pairs_json

    # TODO 未测试 嵌套的场景
    def pairwise(self, data):
        parameters = OrderedDict(data)
        remark_list = list()
        for remark in AllPairs(parameters, n=2, filter_func=self.__is_valid):
            remark_list.append(self.format_pair(remark))
        return remark_list

    # 将1个 需要split的字段分割成kv对
    def split_remark(self, f_remark):
        char_entire = ' '  # 区分字段名和键值对
        char_num = ' '  # 键值对之间
        char_kv = ':'  # 键值对之内
        kv_list = f_remark.split(char_entire, 1)[1].split()  # ['1:开启' '2:关闭']
        key_list = list()
        for kv in kv_list:
            key = kv.split(char_kv)[0]
            key_list.append(key)
        return key_list

    def gen_cases(self, data, gen_strategy):
        print("PairwiseCaseMaker暂未实现")
        pass

    # 备用
'''
    def parse(self, data):
        # 公共解析的部分
        # gen_pre_common()
        final_data = []
        # 如果是form，就是数组
        # api_data = data[0]

        # 如果是json，就是字典
        api_data = data
        api_method = api_data.get('method').lower()
        api_type = api_data.get('variable_type')
        api_data_json = dict(api_data.get('swagger_json_variable'))  # 当json时

        # TODO get-param 二期内容,等前端允许输入remark字段再说
        # TODO 区分restful风格、非restful风格单入参，非restful多入参
        if api_method == 'get':
            # TODO raise SwaggerParseError(
            pass
        # TODO post-data 二期内容
        elif api_method == 'post' and api_type == 'data':
            # TODO raise SwaggerParseError(
            pass

        # post-json
        elif api_method == 'post' and api_type == 'json':

            # 5 建模
            # TODO 使用copy拷贝对象 避免被改动
            api_data_json_copy = copy.copy(api_data_json)
            api_data_model = self.modeling(api_data_json_copy)
            print("\n0 建模后的 api_data_model")
            print(api_data_model)

            # 1 将字典分别拆到multi字典和param字典
            # {'id': {'type': 'integer', 'format': 'int32', 'remark': '主键1:第12:第2'}, 'locationId': {'type': 'integer', 'format': 'int32', 'remark': '类型1:东方2:西方3:南方4:北方'}, 'pageIndex': {'type': 'string', 'format': 'int32', 'remark': '状态1:开启2:关闭'}, 'pageSize': {'type': 'string', 'format': 'int32', 'remark': '类型1:土建2:高压3:低压'}}
            multi_json = dict()  # 多值字典 要智能生成用例
            # {'status': {'type': 'integer', 'format': 'int32', 'remark': '状态'}}
            fixed_json = dict()  # 定值字典 用faker造数据
            for field_key, field_value in api_data_json.items():
                if isinstance(field_value, dict):
                    pass
                elif isinstance(field_value, list):
                    raise SwaggerParseError("field_value是列表，暂不支持 ")
                else:
                    raise SwaggerParseError("field_value 既不是字典也不是列表 ")

                format_remark = self.__format(field_value.get('remark'))
                field_value["remark"] = format_remark
                # print(format_remark)
                if self.is_multi_remark(format_remark) is True:
                    multi_json[field_key] = field_value
                else:
                    fixed_json[field_key] = field_value
            print('1：拆解后的 multi_json')
            print(multi_json)
            print('1：拆解后的 fixed_json')
            print(fixed_json)

            # 2 生成定值字典的值，通过 faker
            # TODO 此处逻辑是针对 json 写的，后续form和get 须注意修改
            for f_json_key, f_json_value in fixed_json.items():
                field_type = f_json_value.get("type")
                field_format = f_json_value.get("format")
                if field_type is None or field_type == '':
                    raise SwaggerParseError('没有type字段或为空')
                if field_type == 'string' and field_format == 'date-time':
                    fixed_json[f_json_key] = str(fakerist.date_time())  # "2022-06-18 19:20:21"
                elif field_type == 'string' and field_format == 'string':
                    fixed_json[f_json_key] = fakerist.word()
                elif field_type == 'integer' and field_format == 'int32':
                    fixed_json[f_json_key] = fakerist.numerify()
                elif field_type == '' and field_format == '':
                    fixed_json[f_json_key] = None
                else:
                    fixed_json[f_json_key] = ''
            print('2：赋值后的 fixed_json')
            print(fixed_json)

            # 3生成多值字典的值，通过pairwise
            # 遍历每个key，把value里的remark里的value字符串转成数组，然后赋值给 key的value
            for multi_json_key, multi_json_value in multi_json.items():
                remark_str = multi_json_value.get('remark')
                multi_json[multi_json_key] = self.split_remark(remark_str)
            multi_json_pairwise_list = self.pairwise(multi_json)
            case_num = len(multi_json_pairwise_list)  # 全排列4*3*3=36条，算法优化后12条
            print("3：赋值后的 multi_json_pairwise_list")
            print(multi_json_pairwise_list)

            # 4 合成最终字典
            final_json_list = [{**fixed_json, **multi_json_pairwise_list[i]} for i in range(case_num)]
            print("4：合并后的每一行")
            for i, x in enumerate(final_json_list):
                print(f"{i}: {json.dumps(x, ensure_ascii=False)}")
            print("4：合并后的 final_json_list")
            print(final_json_list)
            return final_json_list
        else:
            raise SwaggerParseError("content-type类型异常，必须是【 】其中3种")
'''


# gener = PairwiseCaseMaker()
gener = SimpleCaseMaker()

if __name__ == '__main__':

    json0000 = {
        "locationId": {
            "type"  : "integer",
            "format": "int32",
            "remark": "类型 东方:东方 西方:西方 南方:南方 北方:北方"
        },
        "status"    : {
            "type"  : "string",
            "format": "int32",
            "remark": "状态   on:开启   off:关闭 xxx：待定"
        }
    }
    end_data_json = {
        "num"                  : 3,
        "-name"                : '新建建站申请',
        "-desc"                : '接口描述',
        "-url"                 : '/location/api/v1.0/assetProjectManage/',
        "variable_type"        : 'json',
        "method"               : "POST",
        "swagger_json_variable": json0000
    }
    final_data = gener.gen_cases(end_data_json)




