import logging
import thread
import time

import cv2

import Images
from multiprocessing import Process

import numpy as np
import psutil

import image_analysis as ia
import server
import time_utils
import MqttClient
from Camera import Camera
from Constants import *
import httpClient


class AnalysisProcess(Process):
    def __init__(self, pipe):
        Process.__init__(self, name="CameraAnalysisProcess")
        self.mean = np.zeros((Camera.IMAGE_HEIGHT, Camera.IMAGE_WIDTH), dtype=np.uint32)


        self.meanCounter = 0
        self.n_people = 0
        self.pipe = pipe
        self.frame_list = []  # List of grayscale people areas extracted from original frame
        self.people_list = []  # List of estimation for amount of people in a frame
        self.camera_name = CAMERA_NAME  # Camera name
        self.heatmapTimer = time.time()
        self.movementTimer = time.time()
        self.hTemperatureTimer = time.time()
        self.submitTimer = time.time()
        self.movement_detected = False
        self.high_temperature_detected = False
        self.last_incomp = bytearray('')


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

        # Motion jpeg server
        thread.start_new(server.startup, (self.camera,))

        while True:
            data = bytearray(self.pipe.recv())
            self.camera.feed_row(data)


    def _get_last_frame(self):
        """
        Gets last frame from the camera, sends corresponding images to invoke stream or analyze threads.
        Every 5 minutes starts new thread to write data to the database.
        """
        self.mean += self.camera.last_frame
        self.meanCounter += 1
        t = time.time()

        if(t - self.heatmapTimer > HEATMAP_SECONDS):
            self.mean /= self.meanCounter
            self.n_people = ia.process_image(self.camera.last_frame_mask, self.camera_name)
            self.camera.masked_heatmap = ia.extract_grayscale(self.mean.astype(dtype=np.uint8), self.camera.last_frame_mask)

            self.makeHeatmap()
            #thread.start_new_thread(self._analyze_frame, ())
            #cleaning
            self.mean.fill(0)
            logging.info("heatmap created with %d frames", self.meanCounter)
            self._submitHeatmap()
            self.meanCounter = 0
            self.heatmapTimer = t

        if t - self.submitTimer > 10:
            self._submitData()
            self.submitTimer = t

        if t - self.movementTimer > 1:
            # detect movement
            average_val = np.sum(self.camera.bg_subscration_frame) / float(Camera.IMAGE_N_PIXELS)
            self.movement_detected = average_val > MD_SENSITIVITY
            # print average_val
            if self.movement_detected: logging.debug("---movement detected----")
            self.movementTimer = t

        if t - self.hTemperatureTimer > 2:
            # high temperature alarm
            self.high_temperature_detected = self.camera.telemetry['raw_max'] > HIGH_TEMPERATURE_ALARM
            if(self.high_temperature_detected): logging.debug("---danger of fire detected-----")
            self.hTemperatureTimer = t


        # bg substraction
        #np.copyto(self.camera.bg_subscration_frame, self.camera.last_frame)


        # cv2.imshow('bg_subscration_frame', cv2.resize(self.camera.bg_subscration_frame, (700,600), interpolation=cv2.INTER_CUBIC))
        # cv2.imshow('tr', cv2.resize(self.camera.masked_heatmap, (700,600), interpolation=cv2.INTER_CUBIC))
        # cv2.waitKey(22)& 0xFF

        # # Drop outliers created by camera calibration from both lists
        # people_list, frame_list = ia.drop_outliers(self.people_list, self.frame_list)
        # if(len(frame_list) != 0):
        #     narr = np.asarray(frame_list).reshape(len(frame_list), -1)
        #     print "make heatmap with", len(frame_list), "frames",
        #     heatmap = ia.make_heatmap_grayscale(narr)
        #     # post data using http
        #     self._submitData(people_list[-1])
        #     self.last_npeople = people_list[-1]
        #
        # #Cleaning list of frames and people
        # self.mean.fill(0)
        # self.frame_list = []
        # self.people_list = []

    # def _analyze_frame(self):
    #     """
    #     Estimates amount of people from black and white image with human temperatures being
    #     black pixels and everything else being whte pixels. Extracts corresonding grayscale regions from
    #     the frame. Appends amount of people and extracted grayscale image to corresponding lists
    #     """
    #     n_people = ia.process_image(self.camera.last_frame_mask, self.camera_name)
    #     thresh_grayscale = ia.extract_grayscale(self.camera.last_frame, self.camera.last_frame_mask)
    #     #Checks if lists are empty
    #     if not self.people_list:
    #         self.people_list.append(n_people)
    #         self.frame_list.append(thresh_grayscale)
    #
    #     #If lists are not empty checks if the new n_people value isn't abnormally different from the previous one
    #     if (self.people_list and np.absolute(n_people-self.people_list[-1]) < 10):
    #         self.people_list.append(n_people)
    #         self.frame_list.append(thresh_grayscale)


    def _submitHeatmap(self):
        def net_thread_func():
            httpClient.submitImageBuffer(Images._colored_heatmap)
            logging.info("done submitting heatmap")
        thread.start_new(net_thread_func, ())


    def _submitData(self):
        """Post processed data to server"""
        def net_thread_func():
            MqttClient.submit_data(self.n_people, 'people')
            MqttClient.submit_data(str(self.high_temperature_detected), 'firedetection')
            MqttClient.submit_data(str(self.movement_detected), 'movementdetection')
            # image_heatmap = bytearray(Images.getBufferedImage(Images._colored_heatmap))
            # MqttClient.submit_data(image_heatmap.__str__(), 'heatmap')
            MqttClient.submit_telemetry(self.camera.telemetry)

            httpClient.submitData(self.n_people,"people_count")
            logging.info("done submitting data")
        thread.start_new(net_thread_func, ())

    def _read_mask_files(self):
        Images.load()

    def makeHeatmap(self):

        # improve contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        clahe = clahe.apply(self.camera.masked_heatmap)

        colored_heatmap = ia.applyCustomColorMap(clahe, cmap=Images.inferno_cropped, reverse=True)
        #colored_heatmap = cv2.resize(colored_heatmap, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        colored_heatmap = ia.remove_bg(colored_heatmap, cmap="inferno_cropped", reverse=True)
        # cv2.imwrite(imagePath + "colored_heatmap.png", colored_heatmap)
        Images.put("colored_heatmap.png", colored_heatmap)

    def extract_grayscale(heatmap, human_mask):
        """ Extracts all regions identified within the range of human temperatures.

        Args:
            frame (numpy.2darray): grayscale frame received from the camera.
            human_mask (numpy.2darray): Bitmap representation of the frame where all people are black and everything else is white.

        Returns:
            numpy.2darray: The return value. Frame where humans are grayscale and everything else is white.
        """
        mask = (255 - human_mask)  # Invert mask
        mask = np.logical_not(mask)  # Create boolean mask
        heatmap[mask] = 255  # Color everything except human regions in white
        return heatmap