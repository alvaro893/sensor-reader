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
    def __init__(self, process_callback, port):
        Thread.__init__(self, name="SerialThread")
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
                bytes_to_read = self.ser.in_waiting

                # data += self.ser.read(bytes_to_read)
                # data = self.consume_data(data)

                data = self.ser.read(bytes_to_read)
                self.process_callback(bytearray(data))

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
