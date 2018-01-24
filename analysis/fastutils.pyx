import cython
from libc.math cimport ceil

#@cython.boundscheck(False)
cpdef void process_row(int n_row, unsigned char [:, :] frame_arr, unsigned char [:] row):
    cdef int f_row, f_col, val, indx, size
    size = row.shape[0] # efficient len()
    for indx in range(0,size):
        val = row[indx]
        f_row = n_row / 2
        f_col = (n_row + 1) % 2 * 80 + indx # 'add 1 to n_row' to reverse order
        frame_arr[f_row, f_col] = val



#@cython.boundscheck(False)
cpdef void find_people(unsigned short [:] in_flat_img, int people_min, int people_max, unsigned char [:] out_flat_img):
    cdef unsigned short x
    """
    Creates an image where everything in human temperature range is black and
    everything else is white.

    Arguments:
        img (narray 16bits): Flattened image from which human temperature areas should be extracted.
        people_min (int): Minimum raw value for a human temperature range.
        people_max (int): Maximum raw value for a human temperature range.
        out_flat_img(narray 8bits): Flattened image where everything in human temperature range is black and
        everything else is white.
    """
    for i in range(0, in_flat_img.shape[0]):
        x = in_flat_img[i]
        if (x < people_max and x > people_min):
            out_flat_img[i] = 255
        else:
            out_flat_img[i] = 0

#@cython.boundscheck(False)
@cython.cdivision(True)
cpdef void rescale_to_raw(unsigned char [:]flat_img, int raw_min, int raw_max, unsigned short [:] out_img_flat):
    #If a frame doesn't have raw_min and raw_max set, assign predifined values
    cdef int leng
    cdef double x,old_min, old_max, old_range, new_range,val
    leng = flat_img.shape[0]
    if raw_min == 0:
        raw_min = 3200
    if raw_max == 0:
        raw_max = 4000

    old_min = 0.0
    old_max = 255.0
    old_range = 255.0
    new_range = (raw_max - raw_min)
    for indx in range(0,leng):
        val = flat_img[indx]
        x = ceil(((val - old_min) * new_range) / old_range) + raw_min
        out_img_flat[indx] = (int)(ceil(x))