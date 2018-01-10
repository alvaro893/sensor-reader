from fileinput import close
from httplib import HTTPConnection, HTTPException
import logging
from threading import Thread
from time import sleep

from Constants import URL

path = "/"

# timeout for each request will be 1 sec
class HttpClient(HTTPConnection):
    def __init__(self):
        HTTPConnection.__init__(self, URL, 80, timeout=1)

    def reconnect(self):
        self.close()
        self.connect()

    def submitData(self, data):
        self._runAsync(lambda: self.request("POST", path, str(data)),
                       self._defaultResponse)

    def submitImage(self, imgPath):
        imagefile = open(imgPath)
        headers = {"Content-Type":"image/png"}
        def responseCallback():
            self._defaultResponse()
            imagefile.close()
        self._runAsync(lambda: self.request("POST", path + "/image", imagefile, headers),
                       responseCallback)

    def _defaultResponse(self):
        res = self.getresponse()
        data = res.read()
        logging.debug("http response %s %s data: %s", str(res.reason), str(res.reason), str(data))

    def _runAsync(self, requestCallback, responseCallback):
        def target():
            try:
                requestCallback(); responseCallback()
            except Exception as e:
                logging.error("http error: %s" + e.message)
                self.reconnect()

        t = Thread(target=target)
        t.start()

