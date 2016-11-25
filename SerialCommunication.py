import serial
import re
import os
from Constants import *
import logging as log
__author__ = 'Alvaro'

port = PORT_LINUX
if os.name == WINDOWS:
    port = PORT_WINDOWS
sequence = INITIAL_SEQUENCE
ser = serial.Serial(port, BAUD_SPEED)
pat = re.compile(sequence)


def _look_patern(data, process_line):
    last = 0
    matches = pat.finditer(data)
    for match in matches:
        # read between FF FF FF
        start = match.start()
        frame = data[last : start]
        last = match.end()
        if(start > 0):
            # do something
            readHex(frame)
            process_line(bytearray(frame))
    frame = data[last:]
    readHex(frame)

def readHex(data):
    print(' '.join(x.encode('hex') for x in data))


def istart(process_line):
    ser.write("*IDN?\n") # this solves the issue of not reading in linux
    bytesToRead = ser.inWaiting()
    lines = ser.read(bytesToRead)
    while True:
        readHex(lines)
        _look_patern(lines, process_line)

    ser.close()

def start(process_line):
    #ser.write("*IDN?\n") # this solves the issue of not reading in linux
    while True:
        data = ser.read_until(sequence)
        readHex(data)
        process_line(bytearray(data))
