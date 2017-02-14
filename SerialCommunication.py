import logging
import os
import threading
from threading import Thread

import serial

from Constants import INITIAL_SEQUENCE, BAUD_SPEED

__author__ = 'Alvaro'


def read_hex(data):
    logging.warn(' '.join(x.encode('hex') for x in data))


class SerialCommunication(Thread):
    def __init__(self, process_callback, port, get_raw_data_only=False):
        Thread.__init__(self, name="SerialThread")
        self.get_raw_data_only = get_raw_data_only
        self.lastline = b''
        self.process_callback = process_callback
        self.ser = serial.Serial(port, BAUD_SPEED)
        self.setDaemon(True)
        self.start()
        print("serial port:", port, " ", BAUD_SPEED, " ", os.name)

    def run(self):
        remains = b''
        while self.ser.is_open:
            try:
                one_byte = self.ser.read(1)  # necessary to block thread (in_waiting method doesn't block)
                n_bytes = self.ser.in_waiting
                bytes_read = one_byte + self.ser.read(n_bytes)

                if self.get_raw_data_only:
                    data = bytes_read
                    self.process_callback(bytearray(data))
                else:
                    data = remains + bytes_read
                    remains = self.consume_data(data)

            except serial.SerialException as e:
                logging.error(e.message)
                if len(data) > 0:
                    pass
                else:
                    break

    def consume_data(self, data):
        machs = data.split(INITIAL_SEQUENCE)
        last_ind = len(machs) - 1
        for ind, line in enumerate(machs):
            if ind == last_ind: continue
            self.process_callback(bytearray(line))
        return machs[-1]


    def start_reading(self):
        Thread.start(self)

    def write_to_serial(self, text):
        if self.ser.is_open:
            self.ser.write(text)

    def stop(self):
        if self.ser.is_open:
            self.ser.close()
