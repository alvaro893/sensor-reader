#!/usr/bin/python
import logging
import thread
from Queue import Queue

import time
from websocket import WebSocketApp, ABNF, WebSocketException
from Constants import URL, CAMERA_PATH, PARAMETERS, PORT
from Raspberry_commands import is_raspberry_command, resetsensor

logging.warning("url %s" % URL)


class WebSocketConnection(WebSocketApp):
    def __init__(self, pipe, url="ws://"+URL+ ":" + str(PORT) + CAMERA_PATH + PARAMETERS):
        WebSocketApp.__init__(self, url,
                              on_message=self.on_message,
                              on_error=self.on_error,
                              on_close=self.on_close,
                              on_open=self.on_open)
        self.should_send_data = False
        self.open_connection = False
        self.pipe = pipe
        print "using", self.url

    def on_message(self, ws, message):
        logging.info("received command:%s, %d bytes", message, len(message))
        if not is_raspberry_command(message) and not self.connection_command(message):
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
                try:
                    data = self.pipe.recv()
                    # receive data from serial process and forward it if allowed
                    if self.should_send_data:
                        self.send_data(data)
                except WebSocketException as wse:
                    self.handleError(wse)
                except IOError as ioe:
                    self.handleError(ioe)
                except EOFError as eof:
                    self.handleError(eof)

        thread.start_new_thread(run, ())

    def handleError(self, err):
        logging.error("Restarting sensor application due to:"+err.message)
        self.stop()
        resetsensor()

    def stop(self):
        self.open_connection = False

    def send_data(self, data):
        if self.open_connection and len(data) != 0:
            self.send(data, opcode=ABNF.OPCODE_BINARY)

    def set_pipe(self, pipe):
        self.pipe = pipe

    def connection_command(self, message):
        command = str(message)
        if(command == 'send_frames'):
            self.should_send_data = True
        elif(command == 'stop_frames'):
            self.should_send_data = False
        else:
            return False
        return True

