#!/usr/bin/python
import re
import thread
import time
from Queue import Queue
from threading import Thread

import websocket
import logging

from Constants import INITIAL_SEQUENCE, WS_URL, CAMERA_PATH, CLIENT_PATH, PARAMETERS

url = WS_URL


class WebSocketConnection():
    def __init__(self, url=WS_URL + CAMERA_PATH + PARAMETERS):
        #websocket.enableTrace(True)
        self.url = url
        self.open_connection = False
        self.queue = Queue(5)
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_open=self.on_open)


    def on_message(self, ws, message):
        logging.warn("received command:%s", message)
        self.callback(message)

    def on_error(self, ws, error):
        logging.error(error)

    def on_close(self, ws):
        self.open_connection = False
        logging.warn("### closed ###")

    def on_open(self, ws):
        self.open_connection = True
        logging.warn("opened new socket")

    def stop(self):
        self.open_connection = False

    def send_data(self, data):
        if self.open_connection and len(data) != 0:
            self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)

    def set_callback(self, callback):
        self.callback = callback
