import copy
import re
import json
from collections import OrderedDict
from allpairspy import AllPairs
from jinja2 import Template
from app.util.error_code import SwaggerParseError
from app.util.faker_util import fakerist
from flask import current_app

# import flatdict

# TODO 暂未引入v['pairwise']字段
# TODO 考虑有限状态机
# TODO 优化全局变量

pairwise_stuff = {}
multi_nums = 0


class CaseMaker:

    # 以友好的json格式输出到控制台
    def jprint(self, data):
        print(json.dumps(data, indent=4, ensure_ascii=False))

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
    def format_remark(self, data):
        tmp2 = self.full_to_half(data.strip())
        return tmp2

    # 判断 remark 字符串是否需要 split 生成多条用例
    def is_multi_remark(self, data):
        f_remark = self.full_to_half(data.strip())
        if f_remark.count(':') > 1 and ' ' in f_remark:
            return True
        else:
            return False


'''
简单用例生成器：
统一用faker，边解析边赋值，生成单条用例
'''
# class SimpleCaseMaker(CaseMaker):
#     # TODO-A
#     #   因为其他key名比如format和remark不是所有字段都提供，所以目前只是通过字典value中是否包含'type'这个key名来判断是否终端节点。
#     #   如果字段中如果不含type字段，当前无法判断是终端节点还是普通节点。
#     def make_model(self, data):
#         if len(data) == 0:
#             raise SwaggerParseError(msg='数据为空')
#         if isinstance(data, dict):
#             for k, v in data.items():
#                 if isinstance(v, dict):
#                     # 当前key判断为字段
#                     # 判断依据：简单粗暴地根据是否有type字段
#                     vkeys = v.keys()
#                     if "type" in v:
#                         if v["type"] == 'integer':
#                             data[k] = 233
#                         elif v["type"] == "string":
#                             if "format" in v:
#                                 if v['format'] == 'date-time':
#                                     # data[k] = str(fakerist.future_datetime())
#                                     data[k] = "2021-02-02"
#                                 else:
#                                     data[k] = "default_string"
#                             else:
#                                 data[k] = "default_string"
#                         else:
#                             data[k] = "default_type"
#                     # 当前key判断为非字段，或者是字段不含type的非法场景
#                     else:
#                         self.make_model(data[k])
#                 elif isinstance(v, list):
#                     v_count = len(v)
#                     if v_count == 0:
#                         raise SwaggerParseError(msg="数组为空异常")
#                     # 兼容value中有数组的场景
#                     for i in range(v_count):
#                         self.make_model(v[i])
#                 elif not isinstance(v, (dict, list)):
#                     # TODO-A
#                     # raise SwaggerParseError(msg="openapi文档解析异常。存在不含type字段的非法终端节点，无法正常解析")
#                     # print(f"{k}#{v}")
#                     pass
#                 else:
#                     raise SwaggerParseError(msg='建模获取value类型时异常')
#         elif isinstance(data, list):
#             data_len = len(data)
#             if data_len == 0:
#                 raise SwaggerParseError(msg="数组为空异常")
#             for j in range(data_len):
#                 self.make_model(data[j])
#         else:
#             raise SwaggerParseError(msg="接口详情解析异常")
#         return data
#
#     def gen_cases(self, api_data):
#         # 解析接口相关信息
#         api_method = api_data.get('method').lower()
#         api_type = api_data.get('variableType')
#         api_json = api_data.get('swagger_json_variable')
#         api_data = api_data.get('json_variable')
#         # api_param = api_data.get('param')
#         api_data_json = copy.deepcopy(api_json)
#
#         # print("\n 原始接口信息")
#         # print(json.dumps(api_data_json, ensure_ascii=False))
#         # if isinstance(api_data_json, dict):
#         #     pass
#         # elif isinstance(api_data_json, list):
#         #     # TODO 一般不会有2层列表的场景，暂时固定取[0]
#         #     # TODO 处理后要外面套一层[]
#         #     api_data_json = api_data_json[0]
#         #     print("暂未测试 openapi接口详情字段是列表的场景")
#         # else:
#         #     raise SwaggerParseError(msg="openapi接口详情字段格式异常")
#         # final_cases = []
#
#         # TODO 未测试
#         if api_method == 'get':
#             pass
#         # TODO
#         elif api_method == 'post' and api_type == 'data':
#             raise SwaggerParseError(msg="暂不支持post的form表单请求")
#         elif api_method == 'post' and api_type == 'json':
#
#             print(json.dumps(api_data_json, ensure_ascii=False))
#             if isinstance(api_data_json, dict):
#                 pass
#             elif isinstance(api_data_json, list):
#                 # TODO 一般不会有2层列表的场景，暂时固定取[0]
#                 # TODO 处理后要外面套一层[]
#                 api_data_json = api_data_json[0]
#                 print("暂未测试 openapi接口详情字段是列表的场景")
#             else:
#                 raise SwaggerParseError(msg="openapi接口详情字段格式异常", status=0)
#
#             final_cases = []
#             # 接口字典数据建模并赋值
#             final_case_dict = self.make_model(api_data_json)
#             print(json.dumps(final_case_dict, ensure_ascii=False))
#             final_cases.append(final_case_dict)
#
#             return final_cases
#
#         else:
#             raise SwaggerParseError(msg="content-type类型异常，必须是【json、data、param】其中3种")


'''
算法用例生成器：
fixed用faker，multi用pairwise
'''


class PairwiseCaseMaker(CaseMaker):

    # def test_flatdict(self, x):
    #     value = flatdict.FlatterDict(x)
    #     return value
    # 备用方案
    # def iter_x(self, x):
    #     if isinstance(x, dict):
    #         for key, value in x.items():
    #             yield (key, value)
    #     elif isinstance(x, list):
    #         for index, value in enumerate(x):
    #             yield (index, value)
    # 用来处理嵌套数组和列表
    # def flat(self, x):
    #     for key, value in self.iter_x(x):
    #         if isinstance(value, (dict, list)):
    #             for k, v in self.flat(value):
    #                 k = f'{key}_{k}'
    #                 yield (k, v)
    #         else:
    #             yield (key, value)

    # 给 pairwise调用

    def __is_valid(self, row):
        field_cur_num = len(row)
        field_max_num = 3
        if field_cur_num >= field_max_num:
            # 一年级 不能匹配 10-13岁
            if "XXX" == row[0] and "中文" == row[1]:
                return False
            else:
                return True
        else:
            return True

    def __change_quote(self, m):
        key = '\"' + str(m.group(1)) + '\"'
        # value = '\"' + str(m.group(2)) + '\"'
        mg = m.group(2)
        value = ''
        if mg.count('\'') > 1:
            value = mg.replace('\'', '\"')
        return f"{key}: {value}"

    # 将返回的pairs对象转成字典格式，给 test_pairwise 调用
    # Pairs(signDate='中国', updateUserName='1')
    # {'gnDate': '中国', 'updateUserName': '1'}
    def format_pair(self, tmp):
        text1 = str(tmp)
        # lstrip有bug,弃之 
        # text3 = str(tmp).lstrip('Pairs(').rstrip(')')
        text2 = re.sub(pattern='Pairs\(', repl="", string=text1)
        text3 = re.sub(pattern='\)', repl="", string=text2)
        regex_cp = re.compile('([\u4e00-\u9fa5A-Za-z0-9]+)=([\u4e00-\u9fa5A-Za-z0-9\'\s]+)')
        pairs = '{' + regex_cp.sub(self.__change_quote, text3) + '}'
        pairs_json = json.loads(pairs)
        return pairs_json

    def pairwise(self, data):
        parameters = OrderedDict(data)
        max_threshold = 2 if len(parameters) > 1 else 1
        remark_list = list()
        for remark in AllPairs(parameters, n=max_threshold):  # filter_func=self.__is_valid
            remark_list.append(self.format_pair(remark))
        return remark_list

    # 将1个 需要split的字段分割成kv对
    def split_remark(self, data):
        f_remark = self.format_remark(data)
        char_entire = ' '  # 区分字段名和键值对
        # char_num = ' '  # 键值对之间
        char_kv = ':'  # 键值对之内
        f_remark_items = f_remark.split(char_entire, 1)
        f_remark_right = f_remark_items[1]
        if f_remark_right.count(':') < 1:
            raise SwaggerParseError(msg="备注remark右侧文本 不符合规范")
        kv_list = f_remark_right.split()  # ['1:开启' '2:关闭']
        key_list = list()
        for kv in kv_list:
            key = kv.split(char_kv)[0]
            key_list.append(key)
        return key_list

    # 因为其他key名比如format和remark不是所有字段都提供，所以目前只是通过字典value中是否包含'type'这个key名来判断是否终端节点。
    # 如果字段中如果不含type字段，当前无法判断是终端节点还是普通节点。
    def make_model(self, data):

        global pairwise_item
        global multi_nums

        if len(data) == 0:
            raise SwaggerParseError(msg='数据为空')
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    # vkeys = v.keys()
                    # 当前key判断为字段。判断依据简单粗暴地根据是否有type字段
                    if "type" in v:
                        # 字典中没有remark字段
                        # or remark字段没有提供多候选值
                        # or remark字段有提供多候选值，但不使用pairwise算法扩展用例
                        if ("remark" not in v) or (self.is_multi_remark(v['remark']) is False):
                            # or (self.is_multi_remark(v['remark']) is True and v['pairwise'] == 0):
                            if v["type"] == 'integer':
                                data[k] = fakerist.random_digit()
                            elif v["type"] == "string":
                                if "format" in v:
                                    if v['format'] == 'date-time':
                                        data[k] = str(fakerist.future_datetime(end_date='+3d'))
                                    else:
                                        data[k] = "default_string1"
                                else:
                                    data[k] = "default_string2"
                            else:
                                data[k] = "default_type1"
                        elif (self.is_multi_remark(v['remark']) is True):
                            # and v['pairwise'] == 1:
                            # TODO 要避免key重复 需要用 flatdict
                            data[k] = "{{" + k + "}}"
                            multi_nums += 1
                            # 生成pairwise_item_list，供后续进行pairwise批量生成用例数据
                            pairwise_stuff[k] = self.split_remark(v['remark'])
                        else:
                            pass
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
                    raise SwaggerParseError(msg="openapi文档解析异常。存在不含type字段的非法终端节点，无法正常解析")
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

        # 0。预处理解析接口相关信息
        api_method = api_data.get('method').lower()
        api_type = api_data.get('variableType')
        api_json = api_data.get('swagger_json_variable')
        api_vari = api_data.get('json_variable')
        api_param = api_data.get('param')
        api_data_json = copy.deepcopy(api_json)
        if api_method == 'get':
            raise SwaggerParseError(msg="暂不支持get请求")
        elif api_method == 'post' and api_type == 'data':
            raise SwaggerParseError(msg="暂不支持 post 的 form 表单请求")
        elif api_method == 'post' and api_type == 'json':
            if api_data_json is None or api_data_json == "":
                raise SwaggerParseError(msg="该 post 接口的 swagger_json_variable 字段为空")
            else:
                # 1。生成模版 api_data_model, fixed用faker填充，multi用{{}}，还是嵌套字典
                api_data_model = self.make_model(api_data_json)
                # print(api_data_model)
                if multi_nums == 0:
                    return [api_data_model]
                else:
                    # 2。获取pairwise生成数据所需的物料 pairwise_stuff，并填充到 expect_value_list 列表中
                    api_data_final_list = []
                    global pairwise_stuff
                    expect_value_list = self.pairwise(pairwise_stuff)
                    # print(expect_value_list)
                    # 3。最后套用jinja的render生成数据
                    api_data_model_str = json.dumps(api_data_model, ensure_ascii=False)
                    for expect_value in expect_value_list:
                        api_data_final_str = Template(api_data_model_str).render(expect_value)
                        api_dat_final = json.loads(api_data_final_str)
                        api_data_final_list.append(api_dat_final)
                    return api_data_final_list
        else:
            raise SwaggerParseError(msg="content-type类型异常，必须是【json、data、param】其中3种")



        # 1。生成模版 api_data_model
        # 2。生成 multi_remark_dict 和 fixed_dict
        # 3。flatdict库 将模版 api_data_model 扁平化成 api_data_flatter_model。 用set_delimiter设置分隔符
        # 4。allpairspy库 将api_data_flatter_model 扩展成 api_data_flatter_pairs_list
        # 5。根据 [api_data_flatter_pairs_list] 反扁平化，塞到原始数据中 [api_data_pairs_list]
        # 6。functools库，将 [api_data_pairs_list] 和 [fixed_dict] 相乘，生成api_data_final_list

gener = PairwiseCaseMaker()
# gener = SimpleCaseMaker()

if __name__ == '__main__':

    # 简单版
    # 参考 新增场地  /location/api/v1.0/location/add
    # 参考 新增立项  /location/api/v1.0/assetProjectManage/
    json0000 = {
        "locationId": {
            "type"  : "integer",
            "format": "int32",
            "remark": " 类型 东方:东方 西方:西方 南方:南方 北方:北方"
        },
        "status"    : {
            "type"  : "string",
            "format": "int32",
            "remark": "状态   on:开启   off:关闭 xxx：待定"
        },
        "type"      : {
            "type"  : "string",
            "format": "int32",
            "remark": "类型 1：土建 2：高压 3：低压 "
        },
        "time"      : {
            "type"  : "string",
            "format": "date-time",
            "remark": "时间"
        },
        "shome"     : {
            "type"  : "string",
            "format": "string",
            "remark": "shome"
        },
        "logo"      : {
            "type"  : "integer",
            "format": "int32",
            "remark": "logo"
        }
    }

    # 常规简化版
    # 参考 新增运营文件 /location/api/v1.0/assetProjectFileManage/insertAssetProjectFile
    json0 = {
        "archiveType"   : {
            "type"       : "integer",
            "format"     : "int32",
            "description": "归档类型",
            "refType"    : "",
            "remark"     : "归档类型"
        },
        "signDate"      : {
            "type"       : "string",
            "format"     : "date-time",
            "description": "签订日期",
            "refType"    : "",
            "remark"     : "签订日期"
        },
        "updateUserName": {
            "type"       : "string",
            "description": "更新人姓名",
            "refType"    : "",
            "remark"     : "更新人姓名"
        }
    }

    # 常规版 80%场景
    json1 = {
        "bankAccount"     : {
            "type"   : "string",
            "refType": "",
            "remark" : "银行账号 aaaa:aaaa bbbb:bbbb cccc:cccc "
        },
        "manageAddress"   : {
            "type"   : "string",
            "refType": "",
            "remark" : "经营地址 "
        },
        "supplierFileList": [
            {
                "fileName": {
                    "type"   : "string",
                    "refType": "",
                    "remark" : "经营地址 aaaa:aaaa bbbb:bbbb cccc:cccc"
                },
                "fileUrl" : {
                    "type"   : "string",
                    "refType": "",
                    "remark" : "地址"
                }
            }
        ],
        "otherList"       : [
            {
                "fileName": {
                    "type"   : "string",
                    "refType": "",
                    "remark" : "经营地址"
                },
                "fileUrl" : {
                    "type"   : "string",
                    "refType": "",
                    "remark" : "地址"
                }
            }
        ],
        "uscc"            : {
            "type"   : "string",
            "refType": "",
            "remark" : "统一社会信用代码 "
        }
    }

    # 变态版1，先不管
    json2 = {
        "constructionRequest": {
            "companyId"  : {
                "type"       : "integer",
                "format"     : "int32",
                "description": "公司ID, 即创建单位",
                "refType"    : "",
                "remark"     : "公司ID, 即创建单位"
            },
            "companyName": {
                "type"       : "string",
                "description": "公司名称, 即创建单位名称",
                "refType"    : "",
                "remark"     : "公司名称, 即创建单位名称"
            }
        },
        "stationRequest"     : [
            {
                "civilEngineeringEstimate": {
                    "type"       : "number",
                    "description": "土建估算（元）",
                    "refType"    : "",
                    "remark"     : "土建估算（元）"
                },
                "id"                      : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "建站申请的ID，更新时不能为空",
                    "refType"    : "",
                    "remark"     : "建站申请的ID，更新时不能为空"
                }
            }
        ],
        "fileRequest"        : [
            {
                "id" : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "建站申请的ID，更新时不能为空",
                    "refType"    : "",
                    "remark"     : "建站申请的ID，更新时不能为空"
                },
                "url": {
                    "type"   : "string",
                    "format" : "date-time",
                    "refType": "",
                    "remark" : "文件url"
                }
            },
            {
                "id" : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "建站申请的ID，更新时不能为空",
                    "refType"    : "",
                    "remark"     : "建站申请的ID，更新时不能为空"
                },
                "url": {
                    "type"       : "string",
                    "description": "文件url",
                    "refType"    : "",
                    "remark"     : "文件url"
                }
            },
        ],
    }

    # 变态版2 列表开局
    # 新增租赁用印信息列表  /station/api/v1.0/assetLeaseSign/addLease SignUse SeallnfoList
    json3 = [
        {
            "createTime"                    : {
                "type"   : "string",
                "format" : "date-time",
                "refType": "",
                "remark" : "创建的时间"
            },
            "createUserId"                  : {
                "type"   : "integer",
                "format" : "int32",
                "refType": "",
                "remark" : "创建人id"
            },
            "createUserName"                : {
                "type"   : "string",
                "refType": "",
                "remark" : "创建人姓名"
            },
            "id"                            : {
                "type"   : "integer",
                "format" : "int32",
                "refType": "",
                "remark" : "主键"
            },
            "signId"                        : {
                "type"   : "integer",
                "format" : "int32",
                "refType": "",
                "remark" : "租赁签约信息id"
            },
            "signUseSealFileInfoRequestList": [
                {
                    "createTime"    : {
                        "type"   : "string",
                        "format" : "date-time",
                        "refType": "",
                        "remark" : "创建的时间"
                    },
                    "createUserId"  : {
                        "type"   : "integer",
                        "format" : "int32",
                        "refType": "",
                        "remark" : "创建人id"
                    },
                    "createUserName": {
                        "type"   : "string",
                        "refType": "",
                        "remark" : "创建人姓名"
                    },
                    "id"            : {
                        "type"   : "integer",
                        "format" : "int32",
                        "refType": "",
                        "remark" : "主键"
                    },
                    "isValid"       : {
                        "type"   : "integer",
                        "format" : "int32",
                        "refType": "",
                        "remark" : "是否有效：1：有效，0：无效"
                    },
                    "meanType"      : {
                        "type"   : "integer",
                        "format" : "int32",
                        "refType": "",
                        "remark" : "文件含义"
                    },
                    "name"          : {
                        "type"   : "string",
                        "refType": "",
                        "remark" : "文件名"
                    },
                    "type"          : {
                        "type"   : "string",
                        "refType": "",
                        "remark" : "文件类型"
                    },
                    "updateTime"    : {
                        "type"   : "string",
                        "format" : "date-time",
                        "refType": "",
                        "remark" : "更新的时间"
                    },
                    "updateUserId"  : {
                        "type"   : "integer",
                        "format" : "int32",
                        "refType": "",
                        "remark" : "更新人id"
                    },
                    "updateUserName": {
                        "type"   : "string",
                        "refType": "",
                        "remark" : "更新人姓名"
                    },
                    "url"           : {
                        "type"   : "string",
                        "refType": "",
                        "remark" : "文件url"
                    },
                    "useSealId"     : {
                        "type"   : "integer",
                        "format" : "int32",
                        "refType": "",
                        "remark" : "用印信息id"
                    }
                }
            ],
            "updateTime"                    : {
                "type"   : "string",
                "format" : "date-time",
                "refType": "",
                "remark" : "更新的时间"
            },
            "updateUserId"                  : {
                "type"   : "integer",
                "format" : "int32",
                "refType": "",
                "remark" : "更新人id"
            },
            "updateUserName"                : {
                "type"   : "string",
                "refType": "",
                "remark" : "更新人姓名"
            },
            "useSealCount"                  : {
                "type"   : "integer",
                "format" : "int32",
                "refType": "",
                "remark" : "用印数量"
            },
            "useSealType"                   : {
                "type"   : "integer",
                "format" : "int32",
                "refType": "",
                "remark" : "使用印章类型"
            }
        }
    ]

    # 奇葩场景调试专用
    json9 = {
        "archiveType"                   : {
            "type"  : "string",
            "xxxx"  : "integer",
            "remark": "归档类型"
        },
        "invalidReason"                 : {
            "type"       : "string",
            "description": "作废原因",
            "refType"    : "",
            "remark"     : "作废原因"
        },
        "type"                          : {
            "type"       : "string",
            "description": "作废原因",
            "refType"    : "",
            "remark"     : "作废原因"
        },
        "type2"                         : {
            "xxxxxx": {
                "type"   : "作废原因",
                "refType": "",
                "remark" : "作废原因"
            },
        },
        "lzp"                           : {
            "lzpa": {
                "type"       : "integer",
                "format"     : "int32",
                "description": "归档类型",
                "refType"    : "",
                "remark"     : "归档类型"
            },
            "lzpb": {
                "type"       : "integer",
                "format"     : "int32",
                "description": "归档类型",
                "refType"    : "",
                "remark"     : "归档类型"
            }
        },
        "second"                        : [
            {
                "archiveId": {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "归档信息id",
                    "refType"    : "",
                    "remark"     : "归档信息id"
                },
                "isValid"  : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "是否有效 1：有效 0：无效",
                    "refType"    : "",
                    "remark"     : "是否有效 1：有效 0：无效"
                },
                "meanType" : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "文件含义",
                    "refType"    : "",
                    "remark"     : "文件含义"
                }
            }
        ],
        "signArchiveFileInfoRequestList": [
            {
                "archiveId": {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "归档信息id",
                    "refType"    : "",
                    "remark"     : "归档信息id"
                },
                "isValid"  : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "是否有效 1:有效 0：无效",
                    "refType"    : "",
                    "remark"     : "是否有效 1:有效 0：无效"
                },
                "meanType" : {
                    "type"       : "integer",
                    "format"     : "int32",
                    "description": "文件含义",
                    "refType"    : "",
                    "remark"     : "文件含义"
                }
            }
        ],
        "signDate"                      : {
            "type"       : "string",
            "format"     : "date-time",
            "description": "签订日期",
            "refType"    : "",
            "remark"     : "签订日期"
        },
        "updateUserName"                : {
            "type"       : "string",
            "description": "更新人姓名",
            "refType"    : "",
            "remark"     : "更新人姓名"
        }
    }

    end_data_json = {
        "num": 3,
        "-name": '新建建站申请',
        "-desc": '接口描述',
        "-url": '/location/api/v1.0/assetProjectManage/',
        "variableType": 'json',
        "method": 'POST',
        "swagger_json_variable": json0
    }
    # 主场景测试
    final_data = gener.gen_cases(end_data_json)
    gener.jprint(final_data)
