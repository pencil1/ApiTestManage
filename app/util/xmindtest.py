import json
# from xmindparser import xmind_to_dict
# from xmindparser import xmind_to_json
import os

import xlwt


def readjson(file):
    with open(file, 'r', encoding='utf8') as fr:
        data = json.load(fr)
    return data


def getmkinfo(makers):
    ms = {}
    for m in makers:
        s = m.split('-')
        ms[s[0]] = s[1]
    return ms


def mindtoExcel(xmind_file):
    xmdict = xmind_to_dict(xmind_file)
    title = ['模块', '功能', '用例集', '用例名称', '步骤', '预期结果', '优先级', '测试类型', '备注']
    book = xlwt.Workbook()  # 创建一个excel对象
    sheet = book.add_sheet('Sheet1', cell_overwrite_ok=True)  # 添加一个sheet页
    typemap = {"red": "冒烟测试阶段", "gren": "功能测试阶段"}
    mwhole = xmdict[0].get("topic")
    modulename = mwhole.get("title")
    print(mwhole)
    modulesuit = mwhole.get("topics")
    rownum = 1
    #   print('modulesuit:',modulesuit)
    #    modulename=modulesuit.get("title")
    for i in range(len(title)):  # 将用例表列头写入
        sheet.write(0, i, title[i])
    for m in range(len(modulesuit)):  # 循环字典
        functitle = modulesuit[m].get("title")  # 获取模块标题
        funcsuit = modulesuit[m].get("topics")  # 获取所有的模块
        for c in range(len(funcsuit)):  # 遍历每个模块的用例集
            casesuit = funcsuit[c]
            suittitle = casesuit["title"]
            priority = '2'
            casetype = '功能测试阶段'
            if "makers" in casesuit:  # 如果用例集有标明优先级，则相应的用例优先级取用例集的
                makers = getmkinfo(casesuit["makers"])
                print("makers:", makers)
                if "priority" in makers:
                    priority = makers.get("priority")
                if "star" in makers:
                    casetype = typemap[makers["star"]]
            cases = casesuit.get("topics")  # 获取模块下的用例集合
            for cc in range(len(cases)):  # 遍历每一个用例，获取用例名称、优先级、类型、步骤、预期结果等信息
                caseinfo = []
                caseinfo.append(modulename)
                caseinfo.append(functitle)
                caseinfo.append(suittitle)
                case = cases[cc]
                casetitle = suittitle + case["title"]
                caseinfo.append(casetitle)
                print(isinstance(case, dict))
                print("case:", case)
                if "makers" in case:
                    makers = getmkinfo(case["makers"])
                    print("makers:", makers)
                    if "priority" in makers:
                        priority = makers.get("priority")
                    if "star" in makers:
                        casetype = typemap[makers["star"]]
                lables = []
                if "labels" in case:
                    lables = case["labels"]
                steps = []
                expinfo = []
                if "topics" in case:
                    casestep = case["topics"]
                    for st in range(len(casestep)):
                        step = casestep[st]
                        stepinfo = str(st + 1) + '. ' + step["title"] + '\n'
                        if "topics" in step:
                            stepexp = step["topics"][0]
                            print(stepexp)
                            stepexpinfo = str(st + 1) + '. ' + stepexp["title"] + '\n'
                            expinfo.append(stepexpinfo)
                        steps.append(stepinfo)

                caseinfo.append(steps)
                caseinfo.append(expinfo)
                caseinfo.append(priority)
                caseinfo.append(casetype)
                caseinfo.append(lables)
                print("caseinfo is {}".format(caseinfo))
                for i in range(len(caseinfo)):  # 写入excel
                    print("row is {},i is {}".format(rownum, i))
                    sheet.write(rownum, i, caseinfo[i])
                rownum = rownum + 1
    filename = os.path.abspath(xmind_file[0:-5] + 'xls')
    book.save(filename)
    return filename

if __name__ == '__main__':
    mindtoExcel(r'拆红包.xmind')
