from __future__ import division

import logging
import numpy as np

from SerialCommunication import SerialCommunication
from Utils import int_to_bytes, from_bytes_to_int

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
X_LENGTH_8 = 80
X_LENGTH_2 = 12
DEFAULT_MODE = 8


class HighCamera:

    def __init__(self, port):
        self.frame_arr, self.bit_depth_mode = self.create_empty_matrix(mode=DEFAULT_MODE)
        try:
            self.serial_thread = SerialCommunication(self.process_row, port)
        except Exception as e:
            logging.error(e.message)

        self.bit_depth(DEFAULT_MODE)
    def processData(self, data):
        print(data)

    def create_empty_matrix(self, mode=8):
        if mode == 8:
            x_length = X_LENGTH_8
        elif mode == 2:
            x_length = X_LENGTH_2
        else:
            x_length = 0

        bit_depth_mode = 0
        if mode in {2, 8, 0}:
            bit_depth_mode = mode

        return np.zeros((Y_LENGTH, x_length), dtype=np.uint8), bit_depth_mode


    def process_row(self, row):
        if row < X_LENGTH_8:
            return

        n_row = row[0]
        if n_row < Y_LENGTH:  # normal row
            try:
                data_row = []
                if self.bit_depth_mode == 8:
                    data_row = row[1:X_LENGTH_8 + 1]
                elif self.bit_depth_mode == 2:
                    data_row = row[1:X_LENGTH_2 + 1]
                self.frame_arr[n_row] = np.array(data_row)
            except ValueError as e:
                logging.warn("row size is not suitable: %s", e.message)
        else:  # telemetry row
            self.process_telemetry(row)
            self.process_matrix()

    def process_matrix(self):
        print self.frame_arr

    def process_telemetry(self, data):
        #print len(data), ''.join('{:02x}'.format(x) for x in data)
        if (len(data) < 40):
            return
        telemetry = {}
        telemetry['time_counter'] =           from_bytes_to_int( data[4:6] + data[1:3]) / 1000.0
        telemetry['frame_counter'] =          from_bytes_to_int( data[10:12] + data[7:9] ) / 1000.0
        telemetry['frame_mean'] =             from_bytes_to_int( data[13:15] ) / 1000.0
        telemetry['fpa_temp'] =               from_bytes_to_int( data[16:18] )
        telemetry['raw_max'] =                from_bytes_to_int( data[18:20] )
        telemetry['raw_min'] =                from_bytes_to_int( data[21:23] )
        telemetry['discard_packets_count'] =  from_bytes_to_int( data[24:26] )
        telemetry['raw_max_set'] =            from_bytes_to_int( data[27:29] )
        telemetry['raw_min_set'] =            from_bytes_to_int( data[30:32] )
        telemetry['agc'] =                    from_bytes_to_int( data[33] )
        telemetry['bit_depth'] =              from_bytes_to_int( data[34] )
        telemetry['frame_delay'] =            from_bytes_to_int( data[36:38] )

        # for k,v in telemetry.iteritems():
        #     print k, v

    def send_command(self, cmd, data=''):
        if data == '':
            self.serial_thread.write_to_serial(cmd)
        else:
            arguments = int_to_bytes(int(data))
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
        self.frame_arr, self.bit_depth_mode = self.create_empty_matrix(mode=int(data))
        logging.warn('mode was changed to %d bit depth', self.bit_depth_mode)
        self.send_command('B', data)

    def delay(self, data):
        self.send_command('U', data)

    def stop(self):
        self.serial_thread.stop_reading()
