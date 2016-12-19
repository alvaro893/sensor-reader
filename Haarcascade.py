import cv2
import numpy as np
__author__ = 'Alvaro'

import cv2
import time

face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
cap = cv2.VideoCapture(0) #Open video file

w = cap.get(3) #get width
h = cap.get(4) #get height

mx = int(w/2)
my = int(h/2)

lasttime = 0
count = 0
while(cap.isOpened()):
    count +=1
    ret, frame = cap.read() #read a frame
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            cv2.rectangle(gray, (x,y), (x+w, y+h), (255), 3)
            cv2.putText(gray, "face", (x,y),cv2.FONT_HERSHEY_SIMPLEX
                    ,1,(255,255,255),1,cv2.LINE_AA)
    except Exception as e:
        print e.message
    try:
        text = '%.2f fps' % (count/time.clock())
        cv2.putText(frame, text ,(mx,my),cv2.FONT_HERSHEY_SIMPLEX
                    ,1,(0,0,255),1,cv2.LINE_AA)
        cv2.imshow('Frame',gray)
    except:
        #if there are no more frames to show...
        print('EOF')
        break

    #Abort and exit with 'Q' or ESC
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break
    if k == ord('w'):
        time.sleep(2)

cap.release() #release video file
cv2.destroyAllWindows() #close all openCV windows