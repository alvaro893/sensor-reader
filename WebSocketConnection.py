#!/usr/bin/python
from Queue import Queue
from threading import Thread

import websocket
import thread
import time

class WebSocketConnection(Thread):
    def __init__(self):
        Thread.__init__(self, name=WebSocketConnection.__name__)
        # websocket.enableTrace(True)
        self.open_connection = True
        self.queue = Queue(2)
        self.ws = websocket.WebSocketApp("ws://localhost:8080/camera",
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close,
                                    on_open=self.on_open)
        self.start()

    def run(self):
        while self.open_connection:
            self.ws.run_forever()
            print "try to reconnect in 5 secs"
            time.sleep(5)

    def on_message(self, ws, message):
        print "received command:", message
        if hasattr(self.callback):
            self.callback(message)

    def on_error(self, ws, error):
        print error


    def on_close(self, ws):
        print "### closed ###"


    def on_open(self, ws):
         print "opened"
         def run(*args):
             while self.open_connection:
                ws.send(self.queue.get())
         thread.start_new_thread(run, ())

    def stop(self):
        self.open_connection = False

    def set_callback(self, callback):
        self.callback = callback

    def send_to_socket(self, data):
        if len(data) != 0:
            self.queue.put(data)

# ws = WebSocketConnection()
# while True:
#     print(ws.queue.qsize())
#     ws.queue.put(b'\xff\x56\x67')
#     time.sleep(1)