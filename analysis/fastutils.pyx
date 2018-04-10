import cython
import numpy as np
from libc.math cimport ceil,round

# use "cd analysis && python setup.py build_ext -b .. && cd .." to compile

# ctypedef unsigned char uint8_t
# def process_row(int n_row, unsigned char [:, :] frame_arr, unsigned char [:] row):
#     process_row_fast(n_row,frame_arr,row)
ctypedef unsigned char uint8_t
cdef:
 uint8_t buf[200]
 uint8_t write_buf[200]


@cython.boundscheck(False)
@cython.cdivision(True)
def process_row(unsigned char [:,:] frame_arr, unsigned char [:] row, int flip_horizontal, int flip_vertical):
    """
    n_row: row number
    frame_arr: 2d numpy.ndarray, this is the frame itself
    row: 1d numpy.ndarray, the data row to be processed
    """
    cdef unsigned char val
    cdef int n_row, f_row, f_col, indx, size, frame_height
    n_row = row[0]
    frame_height = frame_arr.shape[0]
    size = row.shape[0]                 # shape is better than len()

    if flip_horizontal == True:
        row= row[1:][::-1]                  # remove the 1st element and invert array
        size += -1
    else:
        row= row[1:]

    for indx in xrange(0,size):     # iterate from the last element to the second "[1]"
        val = row[indx]
        f_row = n_row / 2
        f_col = (n_row + flip_horizontal) % 2 * 80 + indx # 'add 1 to n_row' to reverse order

        if flip_vertical == True:
            frame_arr[frame_height-1- f_row,  f_col] = val # y-axis flipped here
        else:
            frame_arr[f_row,  f_col] = val

@cython.cdivision(True)
cpdef void find_people(unsigned char [:,:] dst_img, unsigned short [:,:] src_img, int people_min, int people_max):
    cdef unsigned short val
    cdef int x,y,indx,img_leng, width, height
    """
    Creates an image where everything in human temperature range is black and
    everything else is white.

    Arguments:
        dst_img(narray 8bits):
        src_img (narray 16bits):
        people_min (int): Minimum raw value for a human temperature range.
        people_max (int): Maximum raw value for a human temperature range.
        everything else is white.
    """
    width = src_img.shape[1]
    height = src_img.shape[0]
    img_leng = width*height

    for indx in xrange(0, img_leng):
        x = indx / width
        y = indx % width
        val = src_img[x, y]
        if (val < people_max and val > people_min):
            dst_img[x, y] = 0
        else:
            dst_img[x, y] = 255

@cython.boundscheck(False)
@cython.cdivision(True)
cpdef void rescale_to_raw(unsigned short [:,:] dst_img, unsigned char [:,:] src_img, int raw_min, int raw_max):
    """ convert 8bit image to original 14bit using the min and max raw temperatures"""
    cdef int x,y,indx,img_leng, width, height
    cdef double new_val,old_min, old_max, old_range, new_range,val
    width = src_img.shape[1]
    height = src_img.shape[0]
    img_leng = width*height

    if raw_min == 0:
        raw_min = 3200
    if raw_max == 0:
        raw_max = 4000

    old_min = 0.0
    old_max = 255.0
    old_range = 255.0
    new_range = (raw_max - raw_min)
    for indx in xrange(0,img_leng):
        x = indx / width
        y = indx % width
        val = src_img[x, y]
        new_val = ceil(((val - old_min) * new_range) / old_range) + raw_min
        dst_img[x, y] = (int)(ceil(new_val))

@cython.boundscheck(False)
@cython.cdivision(True)
cpdef void rescale_to_8bit(unsigned char [:,:] dst_img, unsigned short [:,:] src_img, int min, int max):
    """ convert 8bit image to original 14bit using the min and max raw temperatures"""
    cdef int x,y,indx,img_leng, width, height
    cdef double new_val,old_min, old_max, old_range, new_range,val
    width = src_img.shape[1]
    height = src_img.shape[0]
    img_leng = width*height

    old_min = np.min(src_img)
    old_max = np.max(src_img)
    if min > old_min:
        old_min = min
    if max < old_max:
        old_max = max
    old_range = old_max - old_min
    new_range = 255 # the 8bit range
    for indx in xrange(0,img_leng):
        x = indx / width
        y = indx % width
        val = src_img[x, y]
        new_val = ceil(((val - old_min) * new_range) / old_range)
        dst_img[x, y] = (int)(ceil(new_val))

@cython.boundscheck(False)
@cython.cdivision(True)
cpdef normalize_with_absolute_temp(unsigned short [:,:] dst_img, unsigned short [:,:] src_img, int abs_average):
    cdef int rect_width, rect_height
    cdef double rel_average, normp, summa, elements
    rect_width = 44
    rect_height = 29
    # calculate pixel average of the rectangule
    summa = 0
    elements = 0
    for i in range(57, 57+rect_width):
        for j in range(44, 44+rect_height):
            # debug code, delete it
            #src_img[j,i] = 30000
            # end of debug code
            summa += src_img[i,j]
            elements += 1
    rel_average = summa/elements
    # normalization parameter
    normp = abs_average/rel_average

    # create the normalized image
    for i in range(src_img.shape[0]):
        for j in range(src_img.shape[1]):
            dst_img[i,j] = <unsigned short>round(src_img[i,j] * normp)


@cython.boundscheck(False)
@cython.cdivision(True)
cpdef stream_image(unsigned short [:,:] dst_img, unsigned short [:,:] src_img):
    cdef int val
    for i in range(src_img.shape[0]):
        for j in range(src_img.shape[1]):
            val = src_img[i,j] * 16 #  65025/4000 (40 degrees max)
            if val > 65025:
                val = 65025
            dst_img[i,j] = <unsigned short> val


#cdef extern from "native_serial.h":
#    #Note: use bytearray with the uint8_t * types
#    cpdef void serial_loop()
#    cpdef void serial_setup(const char *portname)
#    cpdef void serial_close()
#    cpdef void serial_to_write(uint8_t *buf, int size)
#    cpdef int serial_get_row(uint8_t *data, int max_bytes)
#    cpdef uint8_t serial_check_for_error()


#cdef void callback(uint8_t *buff, int n, void *f):
#    o = buff[:n]
#    (<object>f)(o)


