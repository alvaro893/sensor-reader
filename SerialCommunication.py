from time import sleep

import serial
import os
import logging
from threading import Thread
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
        data = b''
        while self.ser.is_open:
            try:
                n_bytes = self.ser.in_waiting
                bytes_read = self.ser.read(n_bytes)

                if self.get_raw_data_only:
                    data = bytes_read
                    self.process_callback(bytearray(data))
                else:
                    data += bytes_read
                    data = self.consume_data(data)

            except serial.SerialException as e:
                logging.error(e.message)
                if len(data) > 0:
                    pass
                else:
                    break

    def consume_data(self, data):
        lines = data.split(INITIAL_SEQUENCE)
        if (len(lines) < 1):
            return data

        last = lines.pop()

        for line in lines:
            self.process_callback(bytearray(line))
        return last


    def get_line(self):
        return bytearray(self.lastline)

    def start_reading(self):
        Thread.start(self)

    def write_to_serial(self, text):
        if self.ser.is_open:
            self.ser.write(text)

    def stop_reading(self):
        if self.ser.is_open:
            self.ser.close()
