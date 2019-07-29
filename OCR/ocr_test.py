import time
import dlocr
from flask import Flask
from flask import request, jsonify, make_response, render_template, Response
import os
import cv2
from werkzeug.utils import secure_filename
import regex_str as reo
from web_request import Webrequests
import time
import datetime
from hash_ring import *
import redis
import logging as log
import numpy as np

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024

# 设置允许的文件格式
# ALLOWED_EXTENSIONS = set(['png', 'jpg', 'JPG', 'PNG', 'bmp'])
ALLOWED_EXTENSIONS = set(['png'])
number = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
alphabet = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', ',']
tables = ['C1', 'C2', 'C3', 'C5', 'C6', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'D51', 'D52', 'D53', 'D54']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS



def ocr_interface(upload_path):
    '''

    :return: response
    根据移动端传来的图片进行分析识别，把识别结果返回给移动端
    根据分析的结果，识别金额，房间号，用户id发给后台服务端
    '''
    try:
        start = time.time()
        ocr = dlocr.get_or_create()
        accept_time = str(datetime.datetime.now()).split('.')[0]
        img = cv2.imread(upload_path)
        sp = img.shape
        #print("img shape: ", sp[0], sp[1])
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cont = contours[len(contours) - 1]
        ystart = cont[0][0][1]
        if sp[0] > 250 or sp[1] >= 600:
            img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
            if ystart > 20:
                img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 3)]
            else:
                img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 3)]

        else:
            if ystart > 20:
                img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 2)]
            else:
                img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 2)]

        cv2.imwrite(os.path.join('/home/vision/upload', 'ocr.png'), img)
        bboxes, texts = ocr.detect("/home/vision/upload/ocr.png")
        texts = '\n'.join(texts)
        texts = texts.replace('o', '0')
        texts = texts.replace('O', '0')
        house = reo.find_room(texts)
        tableNo = reo.find_table(texts)
        # 进入截取定位金额字段，获取金额，发送给服务端
        if tableNo in tables:
            house = "AG"
        s = '''
            [{
            "house":"''' + str(house) + '''",
            "tableNo":"''' + str(tableNo) + '''"
            }]
            '''
        print("s: ", s)
        print(f"cost: {(time.time() - start) * 1000}ms")

        # image_data = open(upload_path, "rb").read()
        response = make_response(s)
        response.headers['Content-Type'] = 'application/json '
        # os.system('rm -rf ' + upload_path)
        # return s

        if tableNo in tables and house != " ":
            res = check_money(upload_path=upload_path, response=response, user_id="0000", house=house, tableNo=tableNo, accept_time=accept_time, ocr=ocr)
            if res != None:
                return res
            if res == None:
                return response
        return response
    except Exception as e:
        print(e)


@app.route('/ocr_post', methods=['POST', 'GET'])
def ocr_post():
    print("--------------------------------------------------------------")
    print("་进入post测试接口。。。。 测试获取到的金额")
    user_id = request.form

    return "200 success"


# ་检测金额是否与变化，如果有变化再传送到服务器端进行结算
def check_money(upload_path=None, user_id=None, response=None, house=None, tableNo=None, accept_time=None, ocr=None):
    start = time.time()
    img = cv2.imread(upload_path)
    # img = cv2.imread('static/images/test.png')
    sp = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cont = contours[len(contours) - 1]
    cont = cont.flatten()
    cdata = []
    for i in range(len(cont)):
        if i % 2 == 1:
            cdata.append(cont[i])
    if len(cdata) == 2 and cdata[0] == cdata[1]:
        ystart = int(cdata[0] * 4)
        yend = int(cdata[0] * 8)
    else:
        ymin = int(min(cdata))
        ystart = int(max(cdata))
        if ymin < 30:
            ystart = int(ystart * 2 - ystart/4)
        print("y: ", ystart)
        if int(max(cdata)) < 15:
            yend = int(ystart * 8)
        else:
            yend = int(ystart * 4)


    print("ystart: ",  ystart, yend, sp[1], cdata)
    print(ystart, yend)
    if sp[0] > 250 or sp[1] >= 600:
        if ystart > 20:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        else:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        # img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
    elif sp[0] > 200 and sp[0] <= 250:
        if ystart > 20:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        else:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        # img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
    else:
        if ystart > 20:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        else:
            img = img[ystart:yend, round(sp[1] / 2):sp[1]]
        # img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))

    cv2.imwrite(os.path.join('/home/vision/upload', user_id + '_money.png'), img)
    bboxe, text = ocr.detect("/home/vision/upload/" + user_id + "_money.png")
    print("text: ", text)
    texts = "\n".join(text)
    texts = texts.replace('o', '0')
    texts = texts.replace('O', '0')
    print("oral text: ", texts)
    text = texts.splitlines()
    application = 'GLM'
    if len(text) > 0:
        appli = reo.find_application(texts)
        if appli != " ":
            application = appli
    video = reo.find_video(texts)
    print("video: ", video == " ", type(video), len(video))
    if tableNo == 'C5' and int(texts.count("频")) < 1:
        print("count: ", texts.count("频"))
        return
    print("application: ", application)
    flag = False
    for i in text:
        if len(i) > 2:
            for j in i:
                print("j: ", j)
                if j in number:
                    text = i
                    if text[0:2] == '.频' or text[0] == '3':
                       # if text[0] in numbers:
                       #    return
                        text = text[1:len(text)]
                    text = reo.match_money(text)
                    for k in text:
                        if k not in alphabet:
                            return

                    text = reo.match_sec(text)
                    if text == None:
                        return
                    text = reo.match_money(text)
                    if text == None:
                        return

                    flag = True
                    break
        if flag == True:
            break

    # text = text[0]

    print("cut text: ", text)
    money = ""
    # if text[0] in number:
    #   text = text[1:len(text)]
    for i in text:
        if i in number:
            money += i
    print("money  tt: ", money)
    if len(money) == 2 or len(money) <= 3:
        for j in money:
            if money[0] == '.':
                money = '0' + money
            if j == '.':
                if len(money) == 2 or len(money) <= 3 or money[0] == '0':
                    if money[0] == '.':
                        money = '0' + money
                    prefix = money.split('.')[0]
                    postfix = money.split('.')[1]
                    if len(postfix) > 2:
                        postfix = postfix[0:2]
                    money = prefix + '.' + postfix

    if (len(money) == 2 or len(money) == 3) and money[0] == '0':
        money = money[0] + '.' + money[1]

    bsend = False
    for m in money:
        if m not in number:
            bsend = True
            break
    if len(money) > 3 and money[0] == '.':
        money = money[1:len(money)]

    money = reo.match_postfix(money)
    if money == None:
        return response

    if len(money) > 1 and money[0] != '.' and bsend == False:
        user_app = user_id + application
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
                money = sec[0]+sec[1]
        print("money: ", user_app, money)
        r = redis.Redis("127.0.0.1", 6379, db=0)
        re_money = r.get(user_app)

        if re_money != None:
            re_money = re_money.decode()
            if re_money == money:
                return response
        if money >= 0:
            return
            url = "http://192.168.1.201/asf/fd/settlement/bill/bet/origin/submit"
            # url = "http://127.0.0.1:8888/ocr_post"
            para = {"userOid": user_id, "application": application, "venus": house, "dataTime": accept_time,
                    "balanceBet": money, "accrualBet": "0"}
            headers = {"Content-Type": "application/json"}
            q = Webrequests()
            q.post_json(url, para, headers)
            print("json: ", (url, para, headers))
            r.set(user_app, money)
        m = r.get(user_app)
        if m == None:
            r.set(user_app, money)
        print(f"cost: {(time.time() - start) * 1000}ms")


@app.route('/recognition_account', methods=['POST'])
def recognition_account():
    '''

    :return: response
    根据移动端传来的图片进行分析识别，把识别结果返回给移动端
    根据分析的结果，识别金额，房间号，用户id发给后台服务端
    '''
    try:
        start = time.time()
        ocr = dlocr.get_or_create()
        if request.method == 'POST':
            f = request.files['file']
            if not (f and allowed_file(f.filename)):
                return jsonify({"error": 1001, "msg": "请检查上传的文件"})
            #basepath = os.path.dirname(__file__)  # 当前文件所在路径
            #print("file name: ", f.filename)
            filename = f.filename
            accept_time = str(datetime.datetime.now()).split('.')[0]
            user_id = filename.split('_')[0]

            #print(f"file cost: {(time.time() - start) * 1000}ms")
            print("user_id: ", user_id, ": ", filename)
            upload_path = os.path.join('/home/vision/upload',
                                       secure_filename(f.filename))  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            #print("path: ", upload_path)
            upload_path = os.path.join('/home/vision/upload', 'test.png')  # 注意：没有的文件夹一定要先创建，不然会提示没有该路径
            f.save(upload_path)

            #res = check_money(upload_path=upload_path, user_id=user_id, ocr=ocr)
            #print(f"cost: {(time.time() - start) * 1000}ms")
            #if res == None:
            #    return '''{}'''

            # 使用Opencv转换一下图片格式和名称
            img = cv2.imread(upload_path)

            #img = cv2.imread('static/images/test.png')
            sp = img.shape
            #print("img shape: ", sp[0], sp[1])
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cont = contours[len(contours) - 1]
            ystart = cont[0][0][1]
            if sp[0] > 250 or sp[1] >= 600:
                img = cv2.resize(img, (round(sp[1] / 1.5), round(sp[0] / 1.5)))
                if ystart > 20:
                    img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 3)]
                else:
                    img = img[ystart:round(sp[0] / 4 + 70), 0:round(sp[1] / 3)]

            else:
                if ystart > 20:
                    img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 2)]
                else:
                    img = img[ystart:round(sp[0] / 2 + 70), 0:round(sp[1] / 2)]

            cv2.imwrite(os.path.join('/home/vision/upload', 'ocr.png'), img)
            bboxes, texts = ocr.detect("/home/vision/upload/ocr.png")
            texts = '\n'.join(texts)
            house = reo.find_room(texts)
            tableNo = reo.find_table(texts)
            # 进入截取定位金额字段，获取金额，发送给服务端
            if tableNo in tables:
                house = "AG"

            s = '''
                [{
                "house":"''' + str(house) + '''",
                "tableNo":"''' + str(tableNo) + '''"
                }]
                '''
            print("s: ", s)
            print(f"cost: {(time.time() - start) * 1000}ms")

            # image_data = open(upload_path, "rb").read()
            response = make_response(s)
            response.headers['Content-Type'] = 'application/json '
            # os.system('rm -rf ' + upload_path)
            # return s
            if tableNo in tables:
                res = check_money(upload_path=upload_path, response=response, user_id=user_id, house=house, accept_time=accept_time, ocr=ocr)
                if res != None:
                    return res

            return response
    except Exception as e:
        print(e)


if __name__ == '__main__':
    ocr_interface(upload_path="/home/vision/PycharmProjects/text-detection-ocr/upload/1561968169_162459662544_ocr.png")