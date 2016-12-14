import serial
import os
import logging
from threading import Thread
from Constants import INITIAL_SEQUENCE, BAUD_SPEED

__author__ = 'Alvaro'


def read_hex(data):
    logging.debug(' '.join(x.encode('hex') for x in data))


class SerialCommunication(Thread):
    def __init__(self, process_callback, port):
        Thread.__init__(self, name="SerialThread")
        self.process_callback = process_callback
        self.ser = serial.Serial(port, BAUD_SPEED)
        self.start()
        print("serial port:", port, " ", BAUD_SPEED, " ", os.name)
        # self.daemon = True

    def run(self):
        while self.ser.is_open:
            data = self.ser.read_until(INITIAL_SEQUENCE)
            read_hex(data)
            self.process_callback(bytearray(data))

    def start_reading(self):
        Thread.start(self)

    def write_to_serial(self, text):
        if self.ser.is_open:
            self.ser.write(text)

    def stop_reading(self):
        if self.ser.is_open:
            self.ser.close()
