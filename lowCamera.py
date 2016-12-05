from __future__ import division
import numpy as np

__author__ = 'Alvaro'

raw_min = None
raw_max = None
raw_mean = None
X_LENGTH = 15
Y_LENGTH = 12
SENSOR_POSITIONS = (4, 0, 8)

frame_arr = np.zeros((Y_LENGTH, X_LENGTH), dtype=np.uint8)


def process_telemetry(data):
    global raw_min, raw_max, raw_mean
    raw_min = (data[0] + 256 * data[1]) / 100
    raw_max = (data[3] + 256 * data[4]) / 100
    raw_mean = (data[6] + 256 * data[7]) / 100
    # print "telemetry values: ", raw_min, raw_max, raw_mean


def get_actual_temperature(raw_value, arr_max, arr_min):
    temp = (raw_max - raw_min) * (raw_value / (arr_max - arr_min)) + raw_min
    return temp


def process_frame(raw_frame):
    if len(raw_frame) < 70:
        return

    # conver to bytes
    bytes_matrix = np.array([raw_frame[49:64],
                             raw_frame[33:48],
                             raw_frame[17:32],
                             raw_frame[1:16]])
    sensor_number = raw_frame[0]  # from 1 to 3, must subtract 1 in x_coord

    process_telemetry(np.array(raw_frame[65:]))
    arr_max = bytes_matrix.max()
    arr_min = bytes_matrix.min()

    for j in range(0, 4):
        y_coord = j + SENSOR_POSITIONS[sensor_number - 1]
        for i in range(0, X_LENGTH):
            temp = get_actual_temperature(bytes_matrix[j][i], arr_max, arr_min)
            frame_arr[y_coord][i] = temp

    return frame_arr
