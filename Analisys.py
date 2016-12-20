import numpy as np, cv2
import logging
from threading import Thread
from Queue import Queue
__author__ = 'Alvaro'

scale = 4
class AsyncAnalysis(Thread):
    def __init__(self, array):
        Thread.__init__(self, name="AnalysisThread")
        self.stopped = False
        self.array = array
        self.queue = Queue(10)
        self.daemon = True
        self.start()
        self.max_t = 0
        self.min_t = 0

    def run(self):
        self.as_video()

    def start(self):
        Thread.start(self)

    def set_array(self, array):
        self.array = array

    def stop(self):
        self.stopped = True

    def as_video(self):
        print self.array
        min_t = 15
        max_t = 35
        #window_name, trackbar_max, trackbar_min = createTrackBars(max_t, min_t)
        while not self.stopped:
            self.get_arr_from_queue()
            if(self.array == None):
                continue
            # print "analysis tread", self.queue.qsize()
            # print self.array
            # create a color image using a color map and mapping range values
            #max_t = cv2.getTrackbarPos(trackbar_max, window_name)
            #min_t = cv2.getTrackbarPos(trackbar_min, window_name)

            n = 10 # I add this to get a decimal more of precision. uint8 truncates the numbers
            mapped = np.interp(self.array*n, [min_t*n, max_t*n], [0,255]).astype(np.uint8)
            img = cv2.applyColorMap(mapped, cv2.COLORMAP_JET)

            # open both of resized images (frames)
            #cv2.imshow('original', self.resize(img, cv2.INTER_NEAREST))
            cv2.imshow('cubic interpolation',self.resize(img, cv2.INTER_CUBIC))
            #cv2.imshow('gray', self.resize(self.array, cv2.INTER_CUBIC))

            # time to wait milisecons
            key = cv2.waitKey(5) & 0xFF

            # escape when q key is pushed
            if key == ord("q") or key == ord("Q"):
                break

        cv2.destroyAllWindows()

    def get_arr_from_queue(self):
        if not self.queue.empty() :
            self.array = self.queue.get()
        else:
            logging.info("empty queue")

    def put_arr_in_queue(self, arr):
        self.queue.put(arr)

    def resize(self, img, interpolation):
        w = self.array.shape[1]
        h = self.array.shape[0]
        return cv2.resize(img,(w*scale,h*scale), interpolation = interpolation)

def createTrackBars(max_t, min_t):
    window_name = 'Control'
    trackbar0_name = 'max temp'
    trackbar1_name = 'min temp'
    nothing = lambda x: x
    cv2.namedWindow(window_name)
    cv2.createTrackbar(trackbar0_name, window_name, 0, 100, nothing)
    cv2.createTrackbar(trackbar1_name, window_name, 0, 100, nothing)
    cv2.setTrackbarPos(trackbar0_name,window_name, max_t)
    cv2.setTrackbarPos(trackbar1_name,window_name, min_t)
    return window_name, trackbar0_name, trackbar1_name

