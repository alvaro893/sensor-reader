from multiprocessing import Process

import logging
import psutil

from Constants import HIGH_PRIORITY
from analysis.CameraConnection import CameraConnection


class AnalysisProcess(Process):
    def __init__(self, pipe):
        Process.__init__(self, name="CameraAnalysisProcess")
        self.pipe = pipe
        self.cameraConnection = CameraConnection()
        self.daemon = True
        self.start()
        print "AnalysisProcess started"
        try:
            psutil.Process(self.pid).nice(HIGH_PRIORITY)
        except psutil.AccessDenied as e:
            logging.error("do not have permission to change priority!")


    #Overrides parent
    def run(self):
        while True:
            data = bytearray(self.pipe.recv())
            # print (data)
            self.cameraConnection.receiveData(data)
