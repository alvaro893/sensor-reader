import numpy as np
import cv2
import threading, thread
from Queue import Queue
import time
import copy, logging
import time_utils
from Camera import Camera
import image_analysis as ia
from Constants import CAMERA_NAME, HEATMAP_PATH, MAX_HOUR, MAX_MIN
from httpClient import HttpClient


class CameraConnection():
    def __init__(self):
        self.httpClient = HttpClient()
        self.frame_list = []            #List of grayscale people areas extracted from original frame
        self.people_list = []           #List of estimation for amount of people in a frame
        self.last_npeople = 0           #Estimation for amount of people in the last frame
        self.queue = Queue()            #Queue to hold frames to be sent to the stream
        self.last_frame = None          #Frame to be sent to the stream  
        self.camera_name = CAMERA_NAME  #Camera name
        self.last_hetmap_time = 0
        # self.people_predictor = TimeSeriesPredictor() #Class for time series prediction of people

        self.camera = Camera()
        self.camera.on_frame_ready(self._get_last_frame)


    def _get_last_frame(self):
        """
        Gets last frame from the camera, sends corresponding images to invoke stream or analyze threads.
        Every 5 minutes starts new thread to write data to the database. 
        """      
        #Read and encode stream image (rescaled according to raw_set values, equalized histogram, applied color map)
        img = self.camera.last_frame_stream
        img = cv2.imencode('.jpg', img)[1].tostring()


        # Time conditions to create heatmap
        delta = time.time() - self.last_hetmap_time
        hour = time_utils.get_hour()
        minute = time_utils.get_minute()
        hour_minute = time_utils.get_hour_minute()
        weekday = time_utils.get_weekday()

        # Remember that this disable heatmap after normal hours
        max_hour = int(MAX_HOUR) or 15
        max_min = int(MAX_MIN) or 5
        condition_one = (max_hour > hour > 8) and minute % max_min == 0 and delta > 60
        condition_two = hour_minute == '15:00' and delta > 60
        if (condition_one or condition_two) and weekday < 5:
            thread.start_new_thread(self._analyze_frame, ())
            self.last_hetmap_time = time.time()

        # Drop outliers created by camera calibration from both lists
        people_list, frame_list = ia.drop_outliers(self.people_list, self.frame_list)
        if(len(frame_list) != 0):
            heatmap = ia.make_heatmap_grayscale(np.asarray(frame_list).reshape(len(frame_list), -1))
            # post data using http
            self._submitData(people_list[-1])

        #Cleaning list of frames and people
        #print self.people_list
        self.frame_list = []
        self.people_list = []

    def _analyze_frame(self):
        """
        Estimates amount of people from black and white image with human temperatures being
        black pixels and everything else being whte pixels. Extracts corresonding grayscale regions from
        the frame. Appends amount of people and extracted grayscale image to corresponding lists
        """
        n_people = ia.process_image(self.camera.last_frame_mask, self.camera_name)
        thresh_grayscale = ia.extract_grayscale(self.camera.last_frame_rescaled, self.camera.last_frame_mask)
        #Checks if lists are empty
        if not self.people_list:
            self.people_list.append(n_people)
            self.frame_list.append(thresh_grayscale)
        #If lists are not empty checks if the new n_people value isn't abnormally different from the previous one
        if (self.people_list and np.absolute(n_people-self.people_list[-1]) < 10):
            self.people_list.append(n_people)
            self.frame_list.append(thresh_grayscale)




    # Added this 2 methods
    def _submitData(self, people):
        self.httpClient.submitData(people)
        time.sleep(0.05)
        self.httpClient.submitImage(HEATMAP_PATH)

    def receiveData(self, data):
        # fix rows bigger than 84. some times there is more than 1 row
        # the following code makes sure we get all the rows
        datasize = len(data)
        if(datasize % 84 == 0):
            nrows = datasize/84
            for i in range(nrows):
                raw_row = data[i*84: i*84 + 84]
                row = raw_row[3:] # row without initial sequence
                self.camera.feed_row(row)