from __future__ import division
import numpy as np

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

frame_arr = np.zeros((Y_LENGTH, X_LENGTH))


def processData(data):
    print(data)


def get_absolute_values():
    return 0, 0, 0


def process_row(row):
    n_row = row[0]
    if (n_row == 1): #new frame
        pass
    if (n_row == 240): #next is telemetry
        process_telemetry(row)
    pass


def process_matrix(m):
    pass


def process_telemetry(t):
    pass

