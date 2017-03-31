import thread
import logging
import psutil
import os
from multiprocessing import Process
from serial import Serial, SerialException
from Constants import VERY_HIGH_PRIORITY, HIGH_PRIORITY

class Serial_reader(Serial):
    """" This class read data from sensor in a Thread """

    def __init__(self, pipe, port):
        Serial.__init__(self, port=port, baudrate=115200)
        self.pipe = pipe
        self._start_process()

    def _start_process(self):
        process = Process(name="SerialProcess", target=self._run, args=())
        process.daemon = True
        process.start()
        try:
            psutil.Process(process.pid).nice(VERY_HIGH_PRIORITY)
        except psutil.AccessDenied as e:
            psutil.Process(process.pid).nice(HIGH_PRIORITY)

    def _get_data(self):
        # necessary to block thread (in_waiting method doesn't block)
        one_byte = self.read(1)
        n_bytes = self.in_waiting
        return one_byte + self.read(n_bytes)
    
    def _send_data(self):
        while self.is_open:
            print "waiting for commands"
            data = self.pipe.recv()
            print data
            self.write(data)

    def _run(self):
        thread.start_new_thread(self._send_data, ())
        while self.is_open:
            try:
                data = self._get_data()
                self.pipe.send(data)
            except IOError as ioe:
                logging.error(ioe.message)
                logging.warning("flushing serial")
                self.flush()
                #sleep(0.05)
            except SerialException as se:
                logging.error(se.message)
                self.stop()
                break


    def stop(self):
        if self.is_open:
            self.close()
