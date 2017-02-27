import logging
import numpy as np

from SerialCommunication import SerialCommunication
from WebSocketConnection import WebSocketConnection, SerialThroughWebSocket
def nothing():
    pass

class Camera:
    def __init__(self, port, y_length=0, x_length=0, only_send_data=False):
        #self.frame_arr = np.zeros((y_length, x_length), dtype=np.uint8)
        self.frame_arr = np.zeros((y_length, x_length))
        self.telemetry = {}
        self.stopped = False
        self.network_thread = None
        self.frame_ready = False
        self.last_frame = self.frame_arr
        self.only_send_data = only_send_data
        self.frame_ready_callback = nothing
        if(only_send_data):
            self.serial_thread = SerialCommunication(self.frame_callback, port, get_raw_data_only=True)
            self.network_thread = WebSocketConnection()
        else:
            if port == 'test':
                print 'testing'
            elif port == None:  # no port means that data comes from network
                self.serial_thread = SerialThroughWebSocket(self.frame_callback)
            else:
                self.serial_thread = SerialCommunication(self.frame_callback, port)


    def frame_callback(self, data):
        raise RuntimeError('frame_callback not implemented')

    def stop(self):
        self.stopped = True
        try:
            if self.network_thread is not None:
                self.network_thread.stop()
            if self.serial_thread is not None:
                self.serial_thread.stop()
        except AttributeError as e:
            logging.error(e)

    def on_frame_ready(self, callback):
        """ When a frame is generated the given callback will be executed"""
        self.frame_ready_callback = callback