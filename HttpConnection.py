import requests
import logging as log
import Constants
from threading import Thread
from Queue import Queue

#log.basicConfig(level=log.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
url = Constants.URL
key = Constants.KEY

class NetworkThread(Thread):
    def __init__(self, daemon=True):
        Thread.__init__(self)
        self.queue = Queue(10)
        self.stopped = False
        self.last_parameters = {}
        self.buff = bytearray()
        self.setDaemon(daemon)
        self.start()

    def _add_to_queue(self, data):
        self.queue.put(data, block=False)


    def add_to_buffer(self, raw_frame, buff_size=2048):
        self.buff += raw_frame
        if (len(self.buff) > buff_size):
            #print "network queue", self.queue.qsize()
            if self.queue.full():
                log.warn("network queue is full, dropping last buffer")
                self.queue.get()
            else:
                self._add_to_queue(self.buff)
                self.buff = bytearray()

    def set_callback(self, callback):
        self.callback = callback

    def stop(self):
        self.stopped = True

    def start(self):
        #self.daemon = True
        Thread.start(self)

    def execute_callback(self, parameters):
        if self.last_parameters != parameters:
            if hasattr(self, 'callback'):
                self.callback(parameters)

    def run(self):
        while not self.stopped:
            data = self.queue.get(block=True)
            parameters = post_buffer(data)
            self.execute_callback(parameters)






def get_paremeters():
    r = requests.get(url + '/')
    log.debug(r.status_code, r.headers)
    return r.json()


def post_n_people(n):
    data = {'key': key, 'n_people': n}
    r = requests.post(url + '/people', data=data)
    log.debug("status:%s, headers:%s, url:%s", r.status_code, r.headers, r.url)
    parameters = r.json()
    return parameters


def post_buffer(data):
    r = requests.post(url + '/video/buffer', data=data, headers={'Content-Type': 'application/octet-stream'})
    log.debug("status:%s, headers:%s, url:%s", r.status_code, r.headers, r.url)
    try:
        parameters = r.json()
        log.debug("parameters:" + str(parameters))
    except ValueError as e:
        print e.message
        parameters = {}
    return parameters
