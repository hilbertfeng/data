import time
import datetime
import re

s1 = "2,193,45"
s2 = '16,990.5'
s3 = "45,990,987.75"
s4 = "4,36.5"
s5 = "2343432"
s6 = "5.08.3"
s7 = "5,05.3"
s8 = "1.047.8"
s9 = "5问 232"
i0 = "17928"
i1 = "1792.8"
i2 = "179.28"


def match(s2):
    if s2.count('.') == 1 and len(s2.split('.')[1]) <= 2:
        sec = s2.split('.')[0]
        sec = str(sec)
        if sec.count(',') > 0:
            text = sec.split(',')
            for i in range(1, len(text)):
                if len(text[i]) % 3 != 0:
                    return
    if s2.count('.') >= 1 and len(s2.split('.')[1]) <= 2:
        sec = s2.split('.')
        sec = sec[1:len(sec)-1]
        if len(sec) % 3 != 0:
            return

    else:
        if s2.count(',') > 0:
            text = s2.split(',')
            for i in range(1, len(text)):
                if len(text[i]) % 3 != 0:
                    return

    return s2


def match_postfix(s3):

    if s3.count('.') > 0:
        sec = s3.split('.')[1]
        if len(sec) == 2 and sec[1] != '5':
            return
    return s3


def match_money(texts):
    regex = '[0-9]([^-]*)(\d+)|[0-9]'
    result = re.search(regex, texts)
    if result != None:
        result = result[0]
    elif result == None:
        result = " "
    return result


def check_money(texts):
    money = texts
    if money.count('.') > 0:
        sec = money.split(".")
        money = ""

        for i in range(len(sec)):
            if i == len(sec) - 1:
                if len(sec[i]) != 3:
                    money = money + "." + sec[i]
                else:
                    money = money + sec[i]
            else:
                money += sec[i]
        if len(sec) == 2 and len(sec[1]) > 2:
            money = sec[0] + sec[1]
    return money


def match_redis_data(re_data, data):
    if re_data != None:
        if len(data) >= 3:
            if re_data.count(".") > 0 and data.count(".") < 1:
                postfix = re_data.split(".")[1]
                if len(postfix) == 2:
                    if postfix == data[len(data) - 2:len(data)]:
                        return
                if len(postfix) == 1:
                    if postfix == data[len(data) - 1:len(data)]:
                        return

    return data


#print(match(s1))
# print(match_postfix(s0))
# print(match_money(s9))
print(match_redis_data(i1, "1232.3"))
# print(check_money(s0))