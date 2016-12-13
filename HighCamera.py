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
DISABLED = False


def to_bytes(n):
    s = '%x' % n
    if len(s) & 1:
        s = '0' + s
    return s.decode('hex')


class HighCamera:
    def __init__(self, port):
        self.frame_arr = np.zeros((Y_LENGTH, X_LENGTH))
        try:
            if (not DISABLED):
                self.serial_thread = SerialCommunication(self.process_row, port)
        except Exception as e:
            logging.error(e.message)

    def processData(self, data):
        print(data)

    def process_row(self, row):
        if row < X_LENGTH:
            return

        n_row = row[0]
        if (n_row < Y_LENGTH):  # new frame
            self.frame_arr[n_row] = np.array(row[1:X_LENGTH + 1])
        else:  # next is telemetry
            self.process_telemetry(row)
            self.process_matrix()  # time to use the matrix after reading 240 rows

    def process_matrix(self):
        print self.frame_arr

    def process_telemetry(self, data):
        print len(data), ''.join('{:02x}'.format(x) for x in data)
        if (len(data) < 40):
            return
        # data.pop(0) # remove first element (it's just the frame number)
        time_counter = data[1:3] + data[4:6]
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

    def send_command(self, cmd, data=''):
        if data == '':
            self.serial_thread.write_to_serial(cmd)
        else:
            arguments = to_bytes(int(data))
            send = bytearray(cmd) + arguments
            # print ['{0:x}'.format(x) for x in send], int(data)
            self.serial_thread.write_to_serial(send)

    def sync(self):
        self.send_command('S')

    def calibrate(self):
        self.send_command('C')

    def max_raw(self, data):
        self.send_command('H', data)

    def min_raw(self, data):
        self.send_command('L', data)

    def auto_gain_hi(self):
        self.send_command('A')

    def auto_gain_low(self):
        self.send_command('a')

    def bit_depth(self, data):
        self.send_command('B', data)

    def delay(self, data):
        self.send_command('U', data)

    def stop(self):
        self.serial_thread.stop_reading()
