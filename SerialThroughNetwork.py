import Constants
import requests
import logging
import re
from time import sleep
from Queue import Queue
from threading import Thread

__author__ = 'Alvaro'

# logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
url = Constants.URL


def get_buffer():
    r = requests.get(url + '/video/buffer')
    data = r.content
    logging.debug("data: %s", data)
    return data


class NetworkThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.queue = Queue(50)
        self.parameters = {}
        self.start()

    def get_next_buff(self):
        return self.queue.get()

    def run(self):
        last_buff = None
        while True:
            sleep(0.5)
            buff = get_buffer()
            # check if the buffer is the same than last one
            if buff != last_buff:
                self.queue.put(buff)
            else:
                logging.warn("buffer dropped")
            last_buff = buff


def process_buffer(data, process_frame):
    frames = data.split(Constants.INITIAL_SEQUENCE)
    for frame in frames:
        process_frame(bytearray(frame))


def start(process_frame):
    while True:
        nt = NetworkThread()
        data = nt.get_next_buff()
        process_buffer(data, process_frame)
