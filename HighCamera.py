import logging
import numpy as np
from time import sleep

from Analisys import AsyncAnalysis
from Camera import Camera
from SerialCommunication import SerialCommunication
from Utils import int_to_bytes, from_bytes_to_int

"""
00 01 02 04 ------
Data is arranged on 240(0xF0) rows of 84 bytes(FF FF FF n_row and 80 of data):
FF FF FF 01 <DATA>
FF FF FF 02 <DATA>
FF FF FF 03 <DATA>
...
FF FF FF F0 <DATA>
FF FF FF <TELEMETRY> (38 Bytes)
Where the 4th byte is the number of the row
Every row of the actual picture has 2 rows of the raw data
so the image is 160 x 120 (20198 Bytes)
"""
Y_LENGTH = 240
X_LENGTH_IMAGE = 160
Y_LENGTH_IMAGE = 120
DEFAULT_MODE = 8


class HighCamera(Camera):

    def __init__(self, *args, **kwargs):
        kwargs['y_length'] = Y_LENGTH_IMAGE; kwargs['x_length'] = X_LENGTH_IMAGE
        Camera.__init__(self,  *args, **kwargs)
        self.bit_depth(DEFAULT_MODE)

    def process_row(self, row):
        n_row = row[0]

        if n_row < Y_LENGTH:  # normal row
            try:
                for indx, val in enumerate(row[1:-3]):
                    f_row = (n_row)/2
                    f_col = (n_row) % 2 * 80 + indx
                    self.frame_arr[f_row][f_col] = val

            except ValueError as e:
                logging.warn("row size is not suitable: %s", e.message)
        else:  # telemetry row
            self.process_telemetry(row)
            self.process_frame()

    def process_frame(self):
        #print self.frame_arr
        self.last_frame = self.frame_arr[::-1] #invert
        #self.analysis_thread.put_arr_in_queue(self.frame_arr[::-1])

    def frame_callback(self, raw_data):
        """ the hi-res camera gets one row from serial connection"""
        if self.only_send_data:
            self.network_thread.add_to_buffer(raw_data, buff_size=100990)
        else:
            self.process_row(raw_data)

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

        self.telemetry = telemetry
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
        logging.warn('mode was changed to %d bit depth', int(data))
        self.send_command('B', data)

    def delay(self, data):
        self.send_command('U', data)

    def stop(self):
        self.serial_thread.stop_reading()
        self.network_thread.stop()
