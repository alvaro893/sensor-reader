import logging
import thread
import time
import Images
from multiprocessing import Process

import numpy as np
import psutil

import image_analysis as ia
import time_utils
import MqttClient
from Camera import Camera
from Constants import CAMERA_NAME, HEATMAP_PATH, MAX_HOUR
from Constants import HIGH_PRIORITY
from httpClient import HttpClient


class AnalysisProcess(Process):
    def __init__(self, pipe):
        Process.__init__(self, name="CameraAnalysisProcess")
        self.pipe = pipe
        self.frame_list = []  # List of grayscale people areas extracted from original frame
        self.people_list = []  # List of estimation for amount of people in a frame
        self.camera_name = CAMERA_NAME  # Camera name
        self.printoutTimer = 0
        self.dataTimer = 0

        self.camera = Camera()
        self.camera.on_frame_ready(self._get_last_frame)
        self.daemon = True
        self._read_mask_files()
        self.start()
        logging.info("Started Analysis process, pid:" + str(self.pid))
        try:
            psutil.Process(self.pid).nice(HIGH_PRIORITY)
        except psutil.AccessDenied as e:
            logging.error("do not have permission to change priority!")


    def run(self):
        """
        Process runs here. Receives data from Serial Process through a pipe
        """
        while True:
            # fix rows bigger than 84. some times there is more than 1 row
            # the following code makes sure we get all the rows
            data = bytearray(self.pipe.recv())
            datasize = len(data)
            if (datasize % 84 == 0):
                nrows = datasize / 84
                for i in range(nrows):
                    raw_row = data[i * 84: i * 84 + 84]
                    row = raw_row[3:]  # row without initial sequence
                    self.camera.feed_row(row)


    def _get_last_frame(self):
        """
        Gets last frame from the camera, sends corresponding images to invoke stream or analyze threads.
        Every 5 minutes starts new thread to write data to the database.
        """
        if(time.time() - self.dataTimer > 60):
            thread.start_new_thread(self._analyze_frame, ())
            self.dataTimer = time.time()

        # Drop outliers created by camera calibration from both lists
        people_list, frame_list = ia.drop_outliers(self.people_list, self.frame_list)
        if(len(frame_list) != 0):
            narr = np.asarray(frame_list).reshape(len(frame_list), -1)
            print "make heatmap with", len(frame_list), "frames",
            heatmap = ia.make_heatmap_grayscale(narr)
            # post data using http
            self._submitData(people_list[-1])
            self.last_npeople = people_list[-1]

        #Cleaning list of frames and people
        self.frame_list = []
        self.people_list = []

    def _analyze_frame(self):
        """
        Estimates amount of people from black and white image with human temperatures being
        black pixels and everything else being whte pixels. Extracts corresonding grayscale regions from
        the frame. Appends amount of people and extracted grayscale image to corresponding lists
        """
        n_people = ia.process_image(self.camera.last_frame_mask, self.camera_name)
        thresh_grayscale = ia.extract_grayscale(self.camera.last_frame, self.camera.last_frame_mask)
        #Checks if lists are empty
        if not self.people_list:
            self.people_list.append(n_people)
            self.frame_list.append(thresh_grayscale)

        #If lists are not empty checks if the new n_people value isn't abnormally different from the previous one
        if (self.people_list and np.absolute(n_people-self.people_list[-1]) < 10):
            self.people_list.append(n_people)
            self.frame_list.append(thresh_grayscale)



    def _submitData(self, people):
        """Post processed data to server"""
        MqttClient.submit_data(people, 'people')
        httpClient = HttpClient()
        # httpClient.submitImage(HEATMAP_PATH)
        httpClient.submitImageBuffer(Images.colored_heatmap)
        time.sleep(1)
        httpClient.submitData(people)
        httpClient.close()

    def _read_mask_files(self):
        Images.load()


