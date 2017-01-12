import logging

import numpy as np

from HttpConnection import NetworkThread
from SerialCommunication import SerialCommunication


class Camera:
    def __init__(self, port, y_length=0, x_length=0):
        #self.frame_arr = np.zeros((y_length, x_length), dtype=np.uint8)
        self.frame_arr = np.zeros((y_length, x_length))
        self.telemetry = {}
        self.stopped = False
        self.network_thread = None
        self.frame_ready = False
        self.last_frame = self.frame_arr
        self.network_thread = NetworkThread()
        self.serial_thread = SerialCommunication(self.frame_callback, port)


    def frame_callback(self, data):
        self.network_thread.add_to_buffer(data, buff_size=100990)
        #raise RuntimeError('frame_callback not implemented')

    def stop(self):
        self.network_thread.stop()
        self.serial_thread.stop_reading()