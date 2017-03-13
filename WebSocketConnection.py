#!/usr/bin/python
import logging
import thread
import time
from Queue import Queue
from threading import Thread

import websocket

from Constants import INITIAL_SEQUENCE, WS_URL, CAMERA_PATH, CLIENT_PATH, PARAMETERS

url = WS_URL


class WebSocketConnection(Thread):
    def __init__(self, url=WS_URL + CAMERA_PATH + PARAMETERS):
        Thread.__init__(self, name=WebSocketConnection.__name__)
        self.url = url
        self.is_open = True
        self.queue = Queue(2)
        self.setDaemon(True)
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_open=self.on_open)
        self.start()

    def run(self):
        while self.is_open:
            self.ws.run_forever()
            if self.is_open:
                logging.warn("try to reconnect in 5 secs")
            time.sleep(5)

    def on_message(self, ws, message):
        #logging.debug("received command:", message)
        self.callback(message, directly=True)

    def on_error(self, ws, error):
        logging.error(error)

    def on_close(self, ws):
        logging.warn("### closed ###")
        self.is_open = False

    def on_open(self, ws):
        logging.warn("opened new socket")

        def run(*args):
            while self.is_open:
                ws.send(self.queue.get(), opcode=websocket.ABNF.OPCODE_BINARY)

        thread.start_new_thread(run, ())

    def stop(self):
        self.ws.close()

    def set_callback(self, callback):
        self.callback = callback

    def send_to_socket(self, data):
        if len(data) != 0:
            self.queue.put(data)


class SerialThroughWebSocket(WebSocketConnection):
    """This class acts like a serial reader but uses The websocket connection"""

    def __init__(self, callback, sensor_name):
        WebSocketConnection.__init__(self, url=WS_URL + CLIENT_PATH + PARAMETERS + '&camera_name=' + sensor_name)
        self.name = SerialThroughWebSocket.__name__
        self.callback = callback
        self.remains = b''

    def on_message(self, ws, message):
        """this is asynchronous called, tipicaly data from camera"""
        data = self.remains + message
        self.remains = self._consume_data(data)

    def write_to_serial(self, data):
        """Actually this sends data to socket"""
        logging.warn("sending: %d B", len(data))
        self.send_to_socket(data)

    def _consume_data(self, data):
        # logging.warn(' '.join(x.encode('hex') for x in data))
        machs = data.split(INITIAL_SEQUENCE)
        last_ind = len(machs) - 1
        for ind, line in enumerate(machs):
            if ind == last_ind: continue
            self.callback(bytearray(line))
        return machs[last_ind]
