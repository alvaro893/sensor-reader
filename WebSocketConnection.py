#!/usr/bin/python
import re
from Queue import Queue
from threading import Thread

import websocket
import thread
import time

from Constants import INITIAL_SEQUENCE, WS_URL, CAMERA_PATH, CLIENT_PATH

url = WS_URL


class WebSocketConnection(Thread):
    def __init__(self, url=WS_URL + CAMERA_PATH):
        Thread.__init__(self, name=WebSocketConnection.__name__)
        websocket.enableTrace(True)
        self.url = url
        self.open_connection = True
        self.queue = Queue(2)
        self.ws = websocket.WebSocketApp(self.url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_open=self.on_open,
                                         subprotocols=["binary", "base64"],
                                         header={'Content-Type': 'application/octet-stream'})
        self.start()

    def run(self):
        while self.open_connection:
            self.ws.run_forever()
            print "try to reconnect in 5 secs"
            time.sleep(5)

    def on_message(self, ws, message):
        print "received command:", message
        self.callback(message, directly=True)

    def on_error(self, ws, error):
        print error

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        print "opened new socket"

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


class SerialThroughWebSocket(WebSocketConnection):
    """This class acts like a serial reader but uses The websocket connection"""

    def __init__(self, callback):
        WebSocketConnection.__init__(self, url=WS_URL + CLIENT_PATH)
        self.name = SerialThroughWebSocket.__name__
        self.callback = callback
        self.pattern = re.compile(INITIAL_SEQUENCE)
        self.remains = b''

    def on_message(self, ws, message):
        """this is asynchronous called, tipicaly data from camera"""
        data = self.remains + message
        self.remains = self._consume_data(data)

    def write_to_serial(self, data):
        """Actually this sends data to socket"""
        print "command to send", data
        self.send_to_socket(data)

    def _consume_data(self, data):
        # print ' '.join(x.encode('hex') for x in data)
        machs = self.pattern.split(data)
        last_ind = len(machs) - 1
        for ind, line in enumerate(machs):
            if ind == last_ind: continue
            self.callback(bytearray(line))
        return machs[-1]
