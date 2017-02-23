import logging
import numpy as np

from Camera import Camera
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


class HighCamera(Camera):

    def __init__(self, *args, **kwargs):
        self.params = {
            'sync': self.sync,
            'calibrate': self.calibrate,
            'max_raw': self.max_raw,
            'min_raw': self.min_raw,
            'auto_gain_hi': self.auto_gain_hi,
            'auto_gain_low': self.auto_gain_low,
            'bit_depth': self.bit_depth,
            'delay': self.delay
        }
        kwargs['y_length'] = Y_LENGTH_IMAGE; kwargs['x_length'] = X_LENGTH_IMAGE
        Camera.__init__(self,  *args, **kwargs)
        #self.bit_depth(DEFAULT_MODE)

    def process_row(self, row):
        if(len(row) < 80):
            return
        n_row = row[0]

        if n_row < Y_LENGTH:  # normal row
            try:
                for indx, val in enumerate(row[1:]):
                    f_row = (n_row)/2
                    f_col = (n_row) % 2 * 80 + indx
                    self.frame_arr[f_row][f_col] = val

            except ValueError and IndexError as e:
                logging.warn("row size is not suitable: %s", e.message)
        else:  # telemetry row
            self.process_telemetry(row)
            self.process_frame()

    def process_frame(self):
        self.last_frame = self.frame_arr
        self.frame_arr = np.zeros((Y_LENGTH_IMAGE, X_LENGTH_IMAGE))
        self.frame_ready_callback()
        #self.analysis_thread.put_arr_in_queue(self.frame_arr[::-1])

    def frame_callback(self, raw_data):
        """ the hi-res camera gets one row from serial connection"""
        if self.only_send_data:
            self.network_thread.send_to_socket(raw_data)
            self.network_thread.set_callback(self.network_callback)
        else:
            self.process_row(raw_data)

    def process_telemetry(self, data):
        # print ''.join('-({0:d}){1:02x}'.format(i,x) for i,x in enumerate(data))
        if (len(data) < 40):
            return
        telemetry = {}
        telemetry['time_counter'] =           from_bytes_to_int( data[5:3:-1] + data[2:0:-1])
        telemetry['frame_counter'] =          from_bytes_to_int( data[11:9:-1] + data[8:6:-1] )
        telemetry['frame_mean'] =             from_bytes_to_int( data[14:12:-1] )
        telemetry['fpa_temp'] =               from_bytes_to_int( data[17:15:-1] )
        telemetry['raw_max'] =                from_bytes_to_int( data[20:18:-1] )
        telemetry['raw_min'] =                from_bytes_to_int( data[23:21:-1] )
        telemetry['discard_packets_count'] =  from_bytes_to_int( data[26:24:-1] )
        telemetry['raw_max_set'] =            from_bytes_to_int( data[29:27:-1] )
        telemetry['raw_min_set'] =            from_bytes_to_int( data[32:30:-1] )
        telemetry['agc'] =                    '{:02d}'.format( data[34] )
        telemetry['bit_depth'] =              '{:01d} bits'.format( data[35] )
        telemetry['frame_delay'] =            from_bytes_to_int( data[38:36:-1] )

        self.telemetry = telemetry
        # for k,v in telemetry.iteritems():
        #     print k, v

    def network_callback(self, parameters, directly=False):
        """ when a new commmand is received from network"""
        if directly:
            self.serial_thread.write_to_serial(parameters)
        params = self.params
        if parameters == {}:
            return
        for param, value in parameters.items():
            try:
                if value == '':
                    params[param]()
                else:
                    params[param](value)
            except KeyError as e:
                logging.warn(e.message + ". invalid parameter")


    def send_command(self, cmd, data=''):
        if data == '':
            self.serial_thread.write_to_serial(cmd)
        else:
            n = int(data)
            if n < 256:
                arguments = int_to_bytes(0) + int_to_bytes(n) # most of commands expect 2 bytes, a zero is need when sending only one byte of data
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
        # bit_bepth command data only will accept one byte
        logging.warn('mode was changed to %d bit depth', int(data))
        send = bytearray('B' + int_to_bytes(int(data)))
        self.serial_thread.write_to_serial(send)

    def delay(self, data):
        self.send_command('U', data)
