from __future__ import division
import numpy as np
import logging
from SerialCommunication import SerialCommunication

"""
Every image has 240 rows (19238 bytes) with the following format:
FF FF FF 01 <DATA>
FF FF FF 02 <DATA>
FF FF FF 03 <DATA>
...
FF FF FF F0 <DATA>
FF FF FF <TELEMETRY> (38 Bytes)
Where the 4th byte is the number of the row
"""
Y_LENGTH = 240
X_LENGTH = 80
DISABLED = True
class HighCamera:
    def __init__(self, port):
        self.frame_arr = np.array([[]])
        try:
            if( not DISABLED):
                self.serial_thread = SerialCommunication(self.processData, port)
        except Exception as e:
            logging.error(e.message)

    def processData(data):
        print(data)



    def process_row(self, row):
        n_row = row[0]
        if (n_row < 240): #new frame
            np.append(self.frame_arr, [row[1:]], axis=0)
        else: #next is telemetry
            self.process_telemetry(row)
            self.process_matrix() #time to use the matrix after reading 240 rows


    def process_matrix(self):
        pass


    def process_telemetry(data):
        time_counter = data[0:1] + data[3:4]
        frame_counter = data[6:7] + data[9:10]
        frame_mean = data[12:13]
        fpa_temp = data[15:16]
        raw_max = data[18:19]
        raw_min = data[21:22]
        discard_packets_count = data[24:25]
        raw_max_set = data[27:28]
        raw_min_set = data[30:31]
        agc = data[33]
        bit_depth = data[34]
        frame_delay = data[36:37]
        pass

    def sync(self):
        self.serial_thread.write_to_serial('S')

    def calibrate(self):
        self.serial_thread.write_to_serial('C')

    def max_raw(self, data):
        self.serial_thread.write_to_serial('H' + data)

    def min_raw(self, data):
        self.serial_thread.write_to_serial('L' + data)

    def auto_gain_hi(self):
        self.serial_thread.write_to_serial('A')

    def auto_gain_low(self):
        self.serial_thread.write_to_serial('a')

    def bit_depth(self, data):
        self.serial_thread.write_to_serial('B' + data)

    def delay(self, data):
        self.serial_thread.write_to_serial('U' + data)

    def stop(self):
        self.serial_thread.stop_reading()

