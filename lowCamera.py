from __future__ import division
import numpy as np
import logging
from Analisys import AsyncAnalysis
from HttpConnection import  NetworkThread
from SerialCommunication import SerialCommunication

__author__ = 'Alvaro'

raw_min = [0,0,0]
raw_max = [0,0,0]
raw_mean = [0,0,0]
X_LENGTH = 15
Y_LENGTH = 12
SENSOR_POSITIONS = (4, 0, 8)

class LowCamera:
    def __init__(self, port):
        self.frame_arr = np.zeros((Y_LENGTH, X_LENGTH))
        self.stopped = False
        print port
        try:
            self.network_thread = NetworkThread()
            self.analysis_thread = AsyncAnalysis(self.frame_arr)
            self.serial_thread = SerialCommunication(self.frame_callback, port)
        except Exception as e:
            logging.error(e.message + " in " + __file__)

    def get_absolute_values(self):
        return min(raw_min), max(raw_max), np.mean(raw_mean)


    def process_telemetry(self, data, sensor_number):
        global raw_min, raw_max, raw_mean
        raw_min[sensor_number] = (data[0] + 256 * data[1]) / 100
        raw_max[sensor_number] = (data[3] + 256 * data[4]) / 100
        raw_mean[sensor_number] = (data[6] + 256 * data[7]) / 100
        # print "telemetry values: ", raw_min, raw_max, raw_mean


    def get_actual_temperature(self, raw_value, arr_max, arr_min, sensor_number):
        temp = (raw_max[sensor_number] - raw_min[sensor_number]) * (raw_value / (arr_max - arr_min)) + raw_min[sensor_number]
        return temp

    def frame_callback(self, raw_frame):
        """ sends raw frame to network and call process frame """
        logging.debug(raw_frame)
        self.network_thread.add_to_buffer(raw_frame)
        processed_frame = self.process_frame(raw_frame)
        self.analysis_thread.put_arr_in_queue(processed_frame)


    def process_frame(self,raw_frame):
        if len(raw_frame) < 70:
            return

        # convert to bytes
        bytes_matrix = np.array([raw_frame[49:64],
                                 raw_frame[33:48],
                                 raw_frame[17:32],
                                 raw_frame[1:16]])
        sensor_number = raw_frame[0] - 1 # sensors are numbered from 1 to 3, must subtract 1
        self.process_telemetry(np.array(raw_frame[65:]), sensor_number)
        arr_max = bytes_matrix.max()
        arr_min = bytes_matrix.min()

        for j in range(0, 4):
            y_coord = j + SENSOR_POSITIONS[sensor_number]
            for i in range(0, X_LENGTH):
                temp = self.get_actual_temperature(bytes_matrix[j][i], arr_max, arr_min, sensor_number)
                self.frame_arr[y_coord][i] = temp
        return self.frame_arr

    def stop(self):
        self.stopped = True
        self.network_thread.stop()
        self.analysis_thread.stop()
        self.serial_thread.stop_reading()