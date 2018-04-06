import logging
import thread
from multiprocessing import Process
from time import sleep

import psutil
from serial import Serial, SerialException

from Cache import get_var

VERY_HIGH_PRIORITY, SENSOR_DELAY, SENSOR_MAX_THRESHOLD, SENSOR_MIN_THRESHOLD = \
    get_var("VERY_HIGH_PRIORITY","SENSOR_DELAY","SENSOR_MAX_THRESHOLD","SENSOR_MIN_THRESHOLD")
INITIAL_SEQUENCE = b'\xff\xff\xff'


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

    def consume_data(self, data):
        """ separate lines using regex and the initial sequence"""
        machs = data.split(INITIAL_SEQUENCE)
        last_ind = len(machs) - 1
        for ind, line in enumerate(machs):
            if ind == last_ind: continue
            # send line to analysis process
            self.analysis_pipe.send(line)
        return machs[-1]

    def _send_data_loop_network(self):
        # blocks on receiving data from pipe
        while self.is_open:
            data = self.network_pipe.recv()
            logging.info("received data:" + str(data))
            self.write(data)

    def _send_data_loop_analysis(self):
        # blocks on receiving data from pipe
        while self.is_open:
            data = self.analysis_pipe.recv()
            logging.info("received data:" + str(data))
            self.write(data)

    def _send_initial_commands(self):
        #send a delay of 500 ms, high temp of 4000, low temp of 3200
        self.write(bytearray('U') + int16_to_bytes(SENSOR_DELAY));         sleep(5)
        self.write(bytearray('H') + int16_to_bytes(SENSOR_MAX_THRESHOLD)); sleep(5)
        self.write(bytearray('L') + int16_to_bytes(SENSOR_MIN_THRESHOLD))

    def _run(self):
        # This represents the process
        remains = b''
        thread.start_new_thread(self._send_initial_commands, ())
        thread.start_new_thread(self._send_data_loop_network, ())
        thread.start_new_thread(self._send_data_loop_analysis, ())
        while self.is_open:
            try:
                # blocking reading (in_waiting method doesn't block)
                bytes_read = self.read(300 + self.in_waiting)

                # send raw data directly to websocket
                self.network_pipe.send(bytes_read)

                # separate lines and send to network process
                remains = self.consume_data(remains + bytes_read)

            except SerialException as se:
                logging.error(se.message)
                self.stop()
                break
            except IOError as ioe:
                logging.error(ioe.message)
                logging.warning("flushing serial")
                self.flush()
                #sleep(0.05)


    def stop(self):
        if self.is_open:
            self.close()
