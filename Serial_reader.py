import logging
import thread
from multiprocessing import Process
from time import sleep

import psutil
from serial import Serial, SerialException, STOPBITS_ONE, EIGHTBITS, PARITY_NONE

from Constants import VERY_HIGH_PRIORITY, SENSOR_DELAY, SENSOR_MAX_THRESHOLD, SENSOR_MIN_THRESHOLD


def int16_to_bytes(i):
    n = int(i)
    lowByte = n & 0xff
    highByte = n >> 8
    return bytearray([highByte, lowByte])

class Serial_reader(Serial):
    """" This class read data from sensor in a Thread """

    def __init__(self, network_pipe, analysis_pipe, port):
        Serial.__init__(self, port=port, baudrate=115200)
        self.network_pipe = network_pipe
        self.analysis_pipe = analysis_pipe
        self._start_process()

    def _start_process(self):
        process = Process(name="SerialProcess", target=self._run, args=())
        process.daemon = True
        process.start()
        logging.info("Serial Process started, pid:" + str(process.pid))
        try:
            psutil.Process(process.pid).nice(VERY_HIGH_PRIORITY)
        except psutil.AccessDenied as e:
            logging.error("do not have permission to change priority!")

    def _get_data(self):
        # necessary to block thread (in_waiting method doesn't block)
        one_byte = self.read(1)
        n_bytes = self.in_waiting
        return one_byte + self.read(n_bytes)

    def _send_data_loop(self):
        # blocks on receiving data from pipe
        while self.is_open:
            print "waiting for commands"
            data = self.network_pipe.recv()
            print data
            self.write(data)

    def _send_initial_commands(self):
        #send a delay of 500 ms, high temp of 4000, low temp of 3200
        self.write(bytearray('U') + int16_to_bytes(SENSOR_DELAY));         sleep(5)
        self.write(bytearray('H') + int16_to_bytes(SENSOR_MAX_THRESHOLD)); sleep(5)
        self.write(bytearray('L') + int16_to_bytes(SENSOR_MIN_THRESHOLD))

    def _run(self):
        # This represents the process
        thread.start_new_thread(self._send_initial_commands, ())
        thread.start_new_thread(self._send_data_loop, ())
        while self.is_open:
            try:
                data = self._get_data()
                self.network_pipe.send(data)
                self.analysis_pipe.send(data)
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
