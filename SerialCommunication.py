import serial
import os
from Constants import *
import logging as log
__author__ = 'Alvaro'

port = PORT_LINUX[0]
if os.name == WINDOWS:
    port = PORT_WINDOWS[0]
sequence = INITIAL_SEQUENCE
ser = serial.Serial(port, BAUD_SPEED)
print("serial port:", port, " ", BAUD_SPEED, " ", os.name)

def readHex(data):
    print(' '.join(x.encode('hex') for x in data))


def start(process_line):
    #ser.write("*IDN?\n") # this solves the issue of not reading in linux
    ser.open()
    while ser.is_open:
        data = ser.read_until(sequence)
        readHex(data)
        process_line(bytearray(data))

ser.close()
