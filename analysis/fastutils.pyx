import cython
from libc.math cimport ceil

# ctypedef unsigned char uint8_t
# def process_row(int n_row, unsigned char [:, :] frame_arr, unsigned char [:] row):
#     process_row_fast(n_row,frame_arr,row)


@cython.boundscheck(False)
@cython.cdivision(True)
def process_row(unsigned char [:,:] frame_arr, unsigned char [:] row):
    """
    n_row: row number
    frame_arr: 2d numpy.ndarray, this is the frame itself
    row: 1d numpy.ndarray, the data row to be processed
    """
    cdef unsigned char val
    cdef int n_row, f_row, f_col, indx, size, frame_height
    n_row = row[0]
    row= row[1:][::-1]                  # remove the 1st element and invert array
    size = row.shape[0]                 # shape is better than len()
    frame_height = frame_arr.shape[0]
    for indx in xrange(0,size):     # iterate from the last element to the second "[1]"
        val = row[indx]
        f_row = n_row / 2
        f_col = (n_row + 1) % 2 * 80 + indx # 'add 1 to n_row' to reverse order
        frame_arr[frame_height-1- f_row,  f_col] = val # y-axis flipped here, withouth flipping: frame_arr[f_row,  f_col] = val

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