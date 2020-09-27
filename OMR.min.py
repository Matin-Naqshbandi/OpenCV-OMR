# USAGE
# python OMR.min.py --image images/pencil.jpg

# import the necessary packages
from imutils import contours
import numpy as np
import argparse
import cv2
import psycopg2
import time
import os
import psutil


start_time = time.time()
try:
    connection = psycopg2.connect(user='SMP_USER',
                                  password="8909",
                                  host='127.0.0.1',
                                  port='5432',
                                  database='SMP_DB')
    cursor = connection.cursor()
    postgreSQL_select_Query = "select answer from key"
    cursor.execute(postgreSQL_select_Query)
    answer = cursor.fetchmany(100)
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)


def marked_bubs(value_list):
    markCnt = 0
    marked_bs = []
    for l, m in enumerate(value_list):
        if m > (max(value_list) - max(value_list) * 10 / 100):
            markCnt += 1
            marked_bs.append(value_list[l])
            marked_bs.append(l)
    if markCnt == 1:
        return marked_bs
    else:
        return 0, markCnt


def ak(questionNum):
    try:
        answer_key = answer[questionNum]
    except NameError:
        print("cannot get answer keys!")
    return answer_key


ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="path to the input image")
args = vars(ap.parse_args())
image = cv2.imread(args["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0]
questionCnts = []
for c in cnts:
    (x, y, w, h) = cv2.boundingRect(c)
    ar = w / float(h)
    if w >= 20 and h >= 20 and 0.9 <= ar <= 1.1:
        questionCnts.append(c)

questionCnts = contours.sort_contours(questionCnts, method="top-to-bottom")[0]


def id_checker():
    idnum = ''
    id_validity = 0
    print("ID: ", end="")
    for (count, i1) in enumerate(np.arange(0, len(questionCnts), 80)):
        LeftToRight = contours.sort_contours(questionCnts[i1:i1 + 80], method="left-to-right")[0]
        for (q, i) in enumerate(np.arange(0, len(LeftToRight), 10)):
            top_down = contours.sort_contours(LeftToRight[i:i + 10], method="top-to-bottom")[0]
            questionTotals = []
            for (j, c) in enumerate(top_down):
                mask = np.zeros(thresh.shape, dtype="uint8")
                cv2.drawContours(mask, [c], -1, 255, -1)
                mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                total = cv2.countNonZero(mask)
                questionTotals.insert(j, total)
            bubbles = marked_bubs(questionTotals)
            if bubbles[0] != 0:
                id_validity += 1
                color = (255, 0, 0)
                cv2.drawContours(image, top_down[bubbles[1]], -1, color, 3)
                idnum += str(bubbles[1])
            elif bubbles[1] == 10:
                print("Left Blank or all bubbles are marked")
            else:
                print(bubbles[1], end=" ")
                print("bubbles have been marked")
        if id_validity != 8:
            idnum.clear()
        break
    return idnum


def question_checker():
    questionNum = 0
    question = '{'
    global questionCnts
    for (q, i) in enumerate(np.arange(80, len(questionCnts), 480)):
        questionCnts = contours.sort_contours(questionCnts[i:i + 400], method="left-to-right")[0]
        for (col, d) in enumerate(np.arange(0, len(questionCnts), 100)):
            cnts = contours.sort_contours(questionCnts[d:d + 100], method="top-to-bottom")[0]
            for (q, i) in enumerate(np.arange(0, len(cnts), 4)):
                questionTotals = []
                cnts_a = contours.sort_contours(cnts[i:i + 4], method="left-to-right")[0]
                for (j, c) in enumerate(cnts_a):
                    mask = np.zeros(thresh.shape, dtype="uint8")
                    cv2.drawContours(mask, [c], -1, 255, -1)
                    mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                    total = cv2.countNonZero(mask)
                    questionTotals.insert(j, total)
                bubbles = marked_bubs(questionTotals)
                if bubbles[0] != 0:
                    k = ak(questionNum)[0]
                    if bubbles[1] == k:
                        question += str(bubbles[1]) + ', '
                    else:
                        question += str(bubbles[1]) + ', '
                elif bubbles[1] == 4:
                    question += ', '
                else:
                    question += ', '
                questionNum += 1
        question += '}'
        break
    return question


print(id_checker())
print(question_checker())

print('DONE!')
process = psutil.Process(os.getpid())
memory = process.memory_info().rss / 1048576

print("--- %s seconds ---" % (time.time() - start_time))
print("Memory used: %s MB" % memory)