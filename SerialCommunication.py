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
        self.start()
        print("serial port:", port, " ", BAUD_SPEED, " ", os.name)
        # self.daemon = True

    def run(self):
        usb_buff = b''
        while self.ser.is_open:
            try:
                # bytes_to_read = self.ser.in_waiting
                # if bytes_to_read == 0:
                #     continue
                #print bytes_to_read
                #data = self.ser.read(bytes_to_read)
                data = self.ser.read_until(INITIAL_SEQUENCE)
                self.process_callback(bytearray(data))
                # usb_buff += self.ser.read(bytes_to_read)
                # remains = self.consume_buffer(usb_buff)
                # usb_buff += remains
            except serial.SerialException as e:
                logging.error(e.message)
                break

    def consume_buffer(self, usb_buff):
        lines = usb_buff.split(INITIAL_SEQUENCE)
        # print len(lines)
        remains = lines.pop()
        # read_hex(lines[-1])
        for line in lines:
            #read_hex(line)
            self.process_callback(bytearray(line))

        return remains

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
