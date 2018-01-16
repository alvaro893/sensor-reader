from fileinput import close
from httplib import HTTPConnection, HTTPException
import logging
from threading import Thread
from time import sleep

from Constants import URL, CAMERA_NAME, PORT


# timeout for each request will be 1 sec
class HttpClient(HTTPConnection):
    def __init__(self):
        HTTPConnection.__init__(self, URL, PORT, timeout=1)

    def reconnect(self):
        self.close()
        self.connect()

    def submitData(self, data):
        headers = {"Content-Type":"text/plain"}
        self._runAsync(lambda: self.request("POST", "/people_count?camera_name="+CAMERA_NAME, str(data), headers),
                       self._defaultResponse)

    def submitImage(self, imgPath):
        imagefile = open(imgPath)
        headers = {"Content-Type":"image/png"}
        def responseCallback():
            self._defaultResponse()
            imagefile.close()
        self._runAsync(lambda: self.request("POST", "/heatmap?camera_name="+CAMERA_NAME, imagefile, headers),
                       responseCallback)

    def _defaultResponse(self):
        res = self.getresponse()
        data = res.read()
        logging.info("http response %s %s data: %s", str(res.reason), str(res.reason), str(data))

    def _runAsync(self, requestCallback, responseCallback):
        def target():
            try:
                requestCallback(); responseCallback()
            except Exception as e:
                logging.error("http error: %s" + e.message)
                self.reconnect()

        t = Thread(target=target)
        t.start()

