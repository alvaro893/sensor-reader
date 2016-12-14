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
X_LENGTH = 80
DISABLED = False


class HighCamera:

    def __init__(self, port):
        self.frame_arr = np.zeros((Y_LENGTH, X_LENGTH), dtype=np.uint8)
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
        if (n_row < Y_LENGTH):  # normal row
            self.frame_arr[n_row] = np.array(row[1:X_LENGTH + 1])
        else:  # telemetry row
            self.process_telemetry(row)
            self.process_matrix()  # time to use the matrix after reading 240 rows

    def process_matrix(self):
        pass#print self.frame_arr[22]

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

        print telemetry['frame_mean']
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
        self.send_command('B', data)

    def delay(self, data):
        self.send_command('U', data)

    def stop(self):
        self.serial_thread.stop_reading()
