import logging
from httplib import HTTPConnection
from threading import Thread

from Constants import URL, CAMERA_NAME, PORT


# timeout for each request will be 1 sec
from analysis import Images


class HttpClient(HTTPConnection):
    def __init__(self):
        HTTPConnection.__init__(self, URL, PORT, timeout=2)

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

    def submitImageBuffer(self, imgName):
        buf = Images.getBufferedImage(imgName)
        def responseCallback():
            self._defaultResponse()
        self._runAsync(lambda: self.request("POST", "/heatmap?camera_name="+CAMERA_NAME, buf, {"Content-Type":"image/png"}),
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
                logging.error("HTTP: %s",e)
                self.reconnect()

        t = Thread(target=target)
        t.start()

