import serial
import re
import os
import logging as log
__author__ = 'Alvaro'

port = '/dev/ttyACM0'
if os.name == 'nt':
    port = 'COM4'
sequence = b'\xff\xff\xff'
ser = serial.Serial(port, 115200)
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
