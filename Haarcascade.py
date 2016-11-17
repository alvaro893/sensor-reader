import cv2
import numpy as np
__author__ = 'Alvaro'

body_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_upperbody.xml')

cap = cv2.VideoCapture(0)

while True:
    ret, img = cap.read()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bodies = body_cascade.detectMultiScale(gray, 1.3, 5)

    print len(bodies)
    for (x,y,w,h) in bodies:
        cv2.rectangle(img, (x,y), (x+w, y+h), (255,0,0), 2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]

    cv2.imshow('img', img)
    k = cv2.waitKey(50) & 0xff
    if k == ord('q'):
        break