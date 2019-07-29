import time
import dlocr
import cv2
import numpy as np
import os
import regex_str as reo
import logging as log

if __name__ == '__main__':
    ocr = dlocr.get_or_create()
    start = time.time()
    basepath = os.path.dirname(__file__)
    img = cv2.imread("upload/1563244845_164061173163ocr.png")
    sp = img.shape
    print("shpae: ", sp[1], sp[0])
    '''
    cv2.resize(img, (round(sp[0]/3), (round(sp[1]/3))))
    img = img[0:round(sp[0]/8)+40, 0:sp[1]]
    cv2.imwrite('test.png', img)
    '''

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
            ystart = int(ystart * 2 - ystart / 4)
        print("y: ", ystart)
        if int(max(cdata)) < 20:
            yend = int(ystart * 8)
        else:
            yend = int(ystart * 4)

    print("ystart: ", ystart, yend, sp[1], cdata)
    print(ystart, yend)

    img = img[ystart:yend, round(sp[1] / 2):sp[1]]
    # img = cv2.resize(img, (round(sp[0]/1.5), round(sp[1]/1.5)))

    #img = cv2.resize(img, (round(sp[0]),round(sp[1])))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((1, 1), np.uint8)
    gray = cv2.dilate(gray, kernel, iterations=5)
    gray = cv2.erode(gray, kernel, iterations=1)
    ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    gray = cv2.bitwise_not(thresh)
    cv2.imwrite(os.path.join(basepath, 'static/images', 'test.png'), img)

    # 像素取反，变成白字黑底
    #gray = cv2.bitwise_not(gray)
    cv2.imwrite(os.path.join(basepath, 'static/images', 'ocr.png'), img)
    #cv2.imshow("img: ", img)
    bboxes, texts = ocr.detect("static/images/test.png")
    print('\n'.join(texts))
    texts = '\n'.join(texts)
    # print("texts: ",texts)
    house = reo.find_room(texts)
    tableNo = reo.find_table(texts)
    s = '''
           [{
           "house":"''' + str(house) + '''",
           "tableNo":"''' + str(tableNo) + '''"
           }]
           '''
    print("s: ", s)

    print(f"cost: {(time.time() - start) * 1000}ms")
    #cv2.waitKey(0)