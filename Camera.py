import logging

import numpy as np

from HttpConnection import NetworkThread
from SerialCommunication import SerialCommunication
from WebSocketConnection import WebSocketConnection, SerialThroughWebSocket


class Camera:
    def __init__(self, port, y_length=0, x_length=0, only_send_data=False, use_http=False):
        #self.frame_arr = np.zeros((y_length, x_length), dtype=np.uint8)
        self.frame_arr = np.zeros((y_length, x_length))
        self.telemetry = {}
        self.stopped = False
        self.network_thread = None
        self.frame_ready = False
        self.last_frame = self.frame_arr
        self.only_send_data = only_send_data
        self.use_http=use_http
        if(only_send_data):
            self.serial_thread = SerialCommunication(self.frame_callback, port, get_raw_data_only=True)
            if use_http:
                self.network_thread = NetworkThread(daemon=False)
            else:
                self.network_thread = WebSocketConnection()
        else:
            if port == None:
                self.serial_thread = SerialThroughWebSocket(self.frame_callback)
            else:
                self.serial_thread = SerialCommunication(self.frame_callback, port)


    def frame_callback(self, data):
        raise RuntimeError('frame_callback not implemented')

    def stop(self):
        self.network_thread.stop()
        self.serial_thread.stop()