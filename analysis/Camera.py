import logging

import cv2
import numpy as np
from analysis.fastutils import process_row, find_people, rescale_to_raw, normalize_with_absolute_temp, rescale_to_8bit

import image_analysis as ia
from Cache import get_var

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


FLIP_HORIZONTAL, FLIP_VERTICAL = get_var("FLIP_HORIZONTAL", "FLIP_VERTICAL")
def nothing(): pass
def scale_range (input, min, max):
    input += -(np.min(input))
    input /= np.max(input) / (max - min)
    input += min
    return input

class Camera():
    MAX_DATA_ROW = 240
    IMAGE_WIDTH = 160
    IMAGE_HEIGHT = 120
    IMAGE_N_PIXELS = IMAGE_WIDTH*IMAGE_HEIGHT
    ROW_SIZE_2BIT = 13
    ROW_SIZE_8BIT = 81
    NUMBER_OF_ABS_TEMP_READINGS = 20

    def __init__(self):
        self.frame_arr =            np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8)
        self.last_frame_mask =      np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8)
        self.last_frame =           np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8)        #Grayscale image from camera
        self.last_frame_stream =    np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8) #Image to be sent to the stream
        self.bg_subscration_frame = np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8)
        self.masked_heatmap =       np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint8)
        self.last_frame16b =        np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint16)
        self.normalized_frame =     np.empty((self.IMAGE_HEIGHT, self.IMAGE_WIDTH), dtype=np.uint16)
        self.data_row =             np.empty((self.ROW_SIZE_8BIT),                  dtype=np.uint8)
        self.temperature_readings = np.zeros((self.NUMBER_OF_ABS_TEMP_READINGS),    dtype=np.int16)
        self.temperature_readings_indx = 0
        self.substractor = cv2.createBackgroundSubtractorMOG2(history=100,detectShadows=False,varThreshold=10)
        self.telemetry = {}
        self.stopped = False
        self.frame_ready = False
        self.sensor_version = 1.6
        self.frame_ready_callback = nothing
        self.clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(1,1))
        self.last_frame_hash = 0


    def feed_row(self, bytearray_row):
        self.data_row = np.asarray(bytearray_row, dtype=np.uint8)
        # if self.data_row.shape[0] == self.ROW_SIZE_2BIT:
        #     self._process_row(self._process_row_2b(bytearray_row))
        if self.data_row.shape[0] == self.ROW_SIZE_8BIT:
            self._process_row()
            #self.process_row(self.process_row_2b(raw_data))
        else:
            logging.warn("row size is not correct:%d", self.data_row.shape[0])
    
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
        self._process_row(row[:81]) # remove the last 4 bytes
            
    def _process_row(self):
        n_row = self.data_row[0]
        if n_row < self.MAX_DATA_ROW:  # normal row
            # Cython signature: process_row(unsigned char [:,:] frame_arr, unsigned char [:] row, int flip_horizontal, int flip_vertical)
            process_row(self.frame_arr, self.data_row, FLIP_HORIZONTAL, FLIP_VERTICAL)

        else:  # last row is telemetry data, also we got the whole frame
            self._process_telemetry(self.data_row)
            self._process_frame()

    def _get_smooth_abs_temp(self):
        """ Smooth the readings from the absolute temperature sensor by taking the average of the few last readings"""
        self.temperature_readings_indx += 1
        if self.temperature_readings_indx >= self.NUMBER_OF_ABS_TEMP_READINGS:
            self.temperature_readings_indx = 0
        self.temperature_readings[self.temperature_readings_indx] = self.telemetry['center_temp']
        return int(round(self.temperature_readings.mean()))


    def _process_frame(self):
        """
        Generates original grayscale frame, rescaled to raw value and back frame,
        frame to be sent to the stream and frame where areas that fall into human temperature range are
        being black pixels and everything else being white pixels.
        """
        np.copyto(self.last_frame, self.frame_arr)
        # generate the original 14bit image in a 16bit array
        rescale_to_raw(self.last_frame16b, self.last_frame, self.telemetry['raw_min_set'], self.telemetry['raw_max_set'])

        if(self.sensor_version >= 1.7):
        # Normalize the image using the new absolute temperature sensor
            absolute_temp_mean = self._get_smooth_abs_temp()
            normalize_with_absolute_temp(self.normalized_frame, self.last_frame16b, absolute_temp_mean)
            rescale_to_8bit(self.last_frame, self.normalized_frame, self.normalized_frame.min(), self.normalized_frame.max()) #back to 8bit

            # generate masked image based on temperature range
            find_people(self.last_frame_mask, self.normalized_frame, absolute_temp_mean +100, absolute_temp_mean + 500)
        else:
            find_people(self.last_frame_mask, self.last_frame16b, 3800, 4300)

        # not beeing used yet
        #self.last_frame_stream = ia.applyCustomColorMap(self.last_frame)

        # streaming background substraction works if copied
        bg_subscration_frame = self.substractor.apply(self.last_frame)
        np.copyto(self.bg_subscration_frame, bg_subscration_frame)


        self.frame_ready_callback()

        # hash it. (works fast for small array like the frame)
        self.last_frame_hash = hash(self.last_frame.__str__())

        # cv2.imshow('last_frame_mask', cv2.resize(self.last_frame_mask, (800,600), interpolation=cv2.INTER_CUBIC))
        # cv2.imshow('last_frame', cv2.resize(self.last_frame, (800,600), interpolation=cv2.INTER_CUBIC))
        # cv2.waitKey(22)& 0xFF
    
    def on_frame_ready(self, callback):
        """ When a frame is generated the given callback will be executed"""
        self.frame_ready_callback = callback
            
    def _process_telemetry(self, data):
        # print ''.join('-({0:d}){1:02x}'.format(i,x) for i,x in enumerate(data))
        if (len(data) < 40):
            return
        telemetry = {}
        telemetry['time_counter'] =           (data[1] & 0xff) + (data[2] << 8 )+(data[4] & 0xff) + (data[5] << 8)
        telemetry['frame_counter'] =          (data[7] & 0xff) + (data[8] << 8 )+(data[10] & 0xff) + (data[11] << 8)
        telemetry['frame_mean'] =             (data[13] & 0xff) + (data[14] << 8 )
        telemetry['fpa_temp'] =               (data[16] & 0xff) + (data[17] << 8 )
        telemetry['raw_max'] =                (data[19] & 0xff) + (data[20] << 8 )
        telemetry['raw_min'] =                  (data[22] & 0xff) + (data[23] << 8 )
        telemetry['discard_packets'] =          (data[25] & 0xff) + (data[26] << 8 )
        telemetry['raw_max_set'] =              (data[28] & 0xff) + (data[29] << 8)
        telemetry['raw_min_set'] =              (data[31] & 0xff) + (data[32] << 8)
        telemetry['agc'] =                       int(data[34])
        telemetry['bit_depth'] =                 int(data[35])
        telemetry['frame_delay'] =              (data[37] & 0xff) + (data[38] << 8)
        # telemetry['time_counter2'] =            from_bytes_to_int( data[44:42:-1] + data[41:39:-1] )
        # telemetry['frame_state'] =             str(data[46])
        telemetry['sensor_version'] =            int(data[47])
        # print "sensor version:", str(telemetry['sensor_version'])
        self.sensor_version = telemetry['sensor_version']/10.0
        if(self.sensor_version >= 1.7):
            telemetry['abs_sensor_temp'] =          (data[49] & 0xff) + (data[50] << 8)
            telemetry['center_temp'] =              (data[52] & 0xff) + (data[53] << 8)
            telemetry['left_temp'] =                (data[55] & 0xff) + (data[56] << 8)
            telemetry['right_temp'] =               (data[58] & 0xff) + (data[59] << 8)
            # print "center:", str(telemetry['center_temp']/100.0)
            # print "left_temp:", str(telemetry['left_temp']/100.0)
            # print "right_temp:", str(telemetry['right_temp']/100.0)
            # print "abs_sensor_temp:", str(telemetry['abs_sensor_temp']/100.0)
        self.telemetry = telemetry

        
    def stop(self):
        self.stopped = True
