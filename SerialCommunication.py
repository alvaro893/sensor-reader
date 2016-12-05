from threading import Thread
import serial
import os
from Constants import *
import logging

__author__ = 'Alvaro'


def readHex(data):
    logging.debug(' '.join(x.encode('hex') for x in data))


class SerialCommunication(Thread):
    def __init__(self, process_callback):
        Thread.__init__(self)
        port = PORT_LINUX[0]
        if os.name == WINDOWS:
            port = PORT_WINDOWS[0]
        self.process_callback = process_callback
        self.sequence = INITIAL_SEQUENCE
        self.ser = serial.Serial(port, BAUD_SPEED)
        print("serial port:", port, " ", BAUD_SPEED, " ", os.name)
        # self.daemon = True

    def run(self):
        while self.ser.is_open:
            data = self.ser.read_until(self.sequence)
            readHex(data)
            self.process_callback(bytearray(data))

    def start_reading(self):
        # self.ser.write("*IDN?\n") # this solves the issue of not reading in linux
        Thread.start(self)

    def stop_reading(self):
        if (self.ser.is_open):
            self.ser.close()
