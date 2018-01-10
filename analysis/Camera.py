import logging
import numpy as np
import image_analysis as ia

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
        self.frame_arr = np.zeros((Y_LENGTH_IMAGE, X_LENGTH_IMAGE))
        self.telemetry = {}                                                 #Telemetry data for the frame
        self.stopped = False                                                
        self.frame_ready = False                                            
        self.last_frame = self.frame_arr                                    #Grayscale image from camera
        self.last_frame_mask = self.frame_arr                               #Extracted human temperature areas 
        self.last_frame_rescaled = self.frame_arr                           #Frame converted to raw and back
        self.last_frame_stream = self.frame_arr                             #Image to be sent to the stream
        self.frame_ready_callback = nothing                                 


    def feed_row(self, row):
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
                for indx, val in enumerate(reversed_row):
                    f_row = n_row / 2
                    f_col = (n_row + 1) % 2 * 80 + indx # 'add 1 to n_row' to reverse order
                    self.frame_arr[f_row][f_col] = val

            except ValueError and IndexError as e:
                logging.warn("row size is not suitable: %s", e.message)
                
        else:  # last row is telemetry data, also we got the whole frame
            self._process_telemetry(bytearray(row))
            self._process_frame()

    def _process_frame(self):
        """
        Generates original grayscale frame, rescaled to raw value and back frame,
        frame to be sent to the stream and frame where areas that fall into human temperature range are
        being black pixels and everything else being white pixels.
        """
        self.last_frame = self.frame_arr[::-1]  #flip vertically
        self.last_frame_mask, self.last_frame_stream, self.last_frame_rescaled = self._rescale_to_raw(self.last_frame)
        self.frame_arr = np.zeros((Y_LENGTH_IMAGE, X_LENGTH_IMAGE))
        self.frame_ready_callback()
    
    def _rescale_to_raw(self, img):
        """
        Arguments:
            img(numpy.2darray): image to be converted

        Returns:
            people_img (): image with human temperatures regions as black and everything else as white
            stream_img (): colorized and equalized image to be sent to the stream
            rescaled_img (): image rescaled to raw and back and equalized
        """

        #Get min and max values set for the camera
        raw_min = self.telemetry['raw_min_set']
        raw_max = self.telemetry['raw_max_set']

        #If a frame doesn't have raw_min and raw_max set, assign predifined values
        if raw_min == 0:
            raw_min = 3200
        if raw_max == 0:
            raw_max = 4000

        old_min = 0
        old_max = 255
        old_range = 255  
        new_range = (raw_max - raw_min)  

        #Rescale to raw values
        raw_img = [int(np.ceil((((x - old_min) * new_range) / old_range) + raw_min)) for x in img.flatten()]

        def find_people(img, people_min, people_max, raw_max, raw_min):
            """
            Creates an image where everything in human temperature range is black and
            everything else is white.

            Arguments:
                img (list): Flattened image from which human temperature areas should be extracted.
                people_min (int): Minimum raw value for a human temperature range.
                people_max (int): Maximum raw value for a human temperature range.
                raw_max (int): Maximum raw value of the frame.
                raw_max (int): Minimum raw value of the frame.
            Returns:
                res_img(list): Flattened image where everything in human temperature range is black and
                everything else is white.
            """
            res_img = [255 if (x < people_max and x > people_min)  else 0 for x in img]
            return res_img

        def rescale_to_eight_bit(img):
            """
            Rescales input image from raw values to eight bit grayscale image.

            Arguments:
                img (list): Flattened image to be rescaled.

            Returns:
                rescaled_img (list): Flattened rescaled image.
            """
            try:
                rescaled_img = [int(np.ceil((x - raw_min) * 255 / (raw_max-raw_min))) for x in img]
                return rescaled_img
            except ZeroDivisionError as e:
                print e.message
                return img

        #Extract regions with human temperatures
        people_img = find_people(raw_img, 3300, 3500, self.telemetry['raw_min_set'], self.telemetry['raw_max_set'])
        people_img = np.asarray(people_img, dtype=np.uint8).reshape(120,160)
        #Rescale back to eight bit
        rescaled_img = np.asarray(rescale_to_eight_bit(raw_img), dtype=np.uint8).reshape(120,160)
        rescaled_img = ia.hist_equalization(rescaled_img)
        #Create image for the stream
        stream_img = ia.applyCustomColorMap(rescaled_img)
        return people_img, stream_img, rescaled_img
    
    def on_frame_ready(self, callback):
        """ When a frame is generated the given callback will be executed"""
        self.frame_ready_callback = callback
            
    def _process_telemetry(self, data):
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
        telemetry['time_counter2'] =            from_bytes_to_int( data[44:42:-1] + data[41:39:-1] )
        telemetry['frame_state'] =             str(data[46])
        telemetry['sensor_version'] =             str(data[47]/10.0)

        self.telemetry = telemetry
        # for k,v in telemetry.iteritems():
        #     print k, v
        
    def stop(self):
        self.stopped = True
