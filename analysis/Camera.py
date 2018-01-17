import logging
import numpy as np
import image_analysis as ia
from analysis.fastutils import process_row, find_people, rescale_to_raw
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
TWO_BYTES_ROW = 13
EIGHT_BYTES_ROW = 80

def nothing(): pass

class Camera():

    def __init__(self):
        self.frame_arr = np.zeros((Y_LENGTH_IMAGE, X_LENGTH_IMAGE), dtype=np.uint8)
        self.telemetry = {}                                                 #Telemetry data for the frame
        self.stopped = False                                                
        self.frame_ready = False                                            
        self.last_frame = self.frame_arr                                    #Grayscale image from camera
        self.last_frame_mask = self.frame_arr                               #Extracted human temperature areas 
        self.last_frame_stream = self.frame_arr                             #Image to be sent to the stream
        self.frame_ready_callback = nothing                                 


    def feed_row(self, bytearray_row):
        row = np.array(bytearray_row, dtype=np.uint8)
        if len(row) > 0:
            if len(row) <= TWO_BYTES_ROW:
                self._process_row(self._process_row_2b(row))
            else:
                self._process_row(row)
                #self.process_row(self.process_row_2b(raw_data))

    
    def _process_row_2b(self, raw_data):
        """ this method has to be used in process_row function. it generates
        the raw using less data"""
        raw_data_array = bytearray(raw_data)
        row = bytearray()
        n_row = raw_data_array[0]
        data = raw_data_array[1:]
        for byte in data:
            row_chunk = bytearray()
            #byte >>= 1 # remove last bit
            for i in xrange(7):
                right_most_bit = byte & 1
                row_chunk.append(right_most_bit * 255)
                byte >>= 1
            row += (row_chunk)
        row.insert(0, n_row) # insert the rownumber
        return row[:81] # remove the last 4 bytes
            
    def _process_row(self, row):
        if(len(row) < EIGHT_BYTES_ROW):
            return
        n_row = row[0]
        if n_row < Y_LENGTH:  # normal row
            try:
                reversed_row = row[1:][::-1]
                # C code
                process_row(n_row, self.frame_arr, reversed_row)

            except ValueError and IndexError as e:
                logging.warn("row size is not suitable: %s", e.message)
                
        else:  # last row is telemetry data, also we got the whole frame
            self._process_telemetry(row)
            self._process_frame()

    def _process_frame(self):
        """
        Generates original grayscale frame, rescaled to raw value and back frame,
        frame to be sent to the stream and frame where areas that fall into human temperature range are
        being black pixels and everything else being white pixels.
        """
        self.last_frame = self.frame_arr[::-1]  #flip vertically
        #
        # in_data
        flattened_image = self.last_frame.flatten() # in_data
        # out_data
        raw16b_flat_img = np.empty(flattened_image.shape, dtype=np.uint16)
        # C function -- Extract regions with human temperatures
        rescale_to_raw(flattened_image, self.telemetry['raw_min_set'], self.telemetry['raw_max_set'], raw16b_flat_img)

        # out data
        people_img = np.empty(raw16b_flat_img.shape, dtype=np.uint8)
        # C function raw16b_flat_img is in_data --
        find_people(raw16b_flat_img, 3300, 3500, people_img)

        # create mask and colorized frame
        print people_img
        self.last_frame_mask = np.asarray(people_img, dtype=np.uint8).reshape(120,160)
        self.last_frame_stream = ia.applyCustomColorMap(self.last_frame)

        # remove data by filling the frame with zeros
        self.frame_arr = np.zeros((Y_LENGTH_IMAGE, X_LENGTH_IMAGE), np.uint8)
        self.frame_ready_callback()
    
    def on_frame_ready(self, callback):
        """ When a frame is generated the given callback will be executed"""
        self.frame_ready_callback = callback
            
    def _process_telemetry(self, data):
        # print ''.join('-({0:d}){1:02x}'.format(i,x) for i,x in enumerate(data))
        if (len(data) < 40):
            return
        telemetry = {}
        # telemetry['time_counter'] =           from_bytes_to_int( data[5:3:-1] + data[2:0:-1])
        # telemetry['frame_counter'] =          from_bytes_to_int( data[11:9:-1] + data[8:6:-1] )
        # telemetry['frame_mean'] =             from_bytes_to_int( data[14:12:-1] )
        # telemetry['fpa_temp'] =               from_bytes_to_int( data[17:15:-1] )
        # telemetry['raw_max'] =                from_bytes_to_int( data[20:18:-1] )
        # telemetry['raw_min'] =                from_bytes_to_int( data[23:21:-1] )
        # telemetry['discard_packets_count'] =  from_bytes_to_int( data[26:24:-1] )
        telemetry['raw_max_set'] =              (data[28] & 0xff) + (data[29] << 8)
        telemetry['raw_min_set'] =              (data[31] & 0xff) + (data[32] << 8)
        # telemetry['agc'] =                    '{:02d}'.format( data[34] )
        # telemetry['bit_depth'] =              '{:01d} bits'.format( data[35] )
        # telemetry['frame_delay'] =            from_bytes_to_int( data[38:36:-1] )
        # telemetry['time_counter2'] =            from_bytes_to_int( data[44:42:-1] + data[41:39:-1] )
        # telemetry['frame_state'] =             str(data[46])
        # telemetry['sensor_version'] =             str(data[47]/10.0)
        self.telemetry = telemetry

        
    def stop(self):
        self.stopped = True
