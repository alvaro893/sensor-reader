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
        self.open_connection = True
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
        logging.warn("### closed ###")

    def on_open(self, ws):
        logging.warn("opened new socket")

        def run(*args):
            while self.open_connection:
                ws.send(self.queue.get(), opcode=websocket.ABNF.OPCODE_BINARY)

        thread.start_new_thread(run, ())

    def stop(self):
        self.open_connection = False

    def set_callback(self, callback):
        self.callback = callback

    def send_to_socket(self, data):
        if len(data) != 0:
            self.queue.put(data)
