#!/usr/bin/python
import logging
import thread
from Queue import Queue

from websocket import WebSocketApp, ABNF
from Constants import URL, CAMERA_PATH, PARAMETERS
from Raspberry_commands import is_raspberry_command

print "using", URL


class WebSocketConnection(WebSocketApp):
    def __init__(self, pipe, url=URL + CAMERA_PATH + PARAMETERS):
        WebSocketApp.__init__(self, url,
                              on_message=self.on_message,
                              on_error=self.on_error,
                              on_close=self.on_close,
                              on_open=self.on_open)
        self.open_connection = False
        self.pipe = pipe

    def on_message(self, ws, message):
        logging.warn("received command:%s, %d bytes", message[0], len(message))
        if not is_raspberry_command(message):
            self.pipe.send(message)

    def on_error(self, ws, error):
        logging.error(error)

    def on_close(self, ws):
        self.open_connection = False
        logging.warn("### closed ###")

    def on_open(self, ws):
        self.open_connection = True
        logging.warn("opened new socket")

        def run():
            while (self.open_connection == True):
                data = self.pipe.recv()
                self.send_data(data)

        thread.start_new_thread(run, ())

    def stop(self):
        self.open_connection = False

    def send_data(self, data):
        if self.open_connection and len(data) != 0:
            self.send(data, opcode=ABNF.OPCODE_BINARY)

    def set_pipe(self, pipe):
        self.pipe = pipe
