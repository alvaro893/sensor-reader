from __future__ import division
import numpy as np

__author__ = 'Alvaro'

raw_min = [0,0,0]
raw_max = [0,0,0]
raw_mean = [0,0,0]
X_LENGTH = 15
Y_LENGTH = 12
SENSOR_POSITIONS = (4, 0, 8)

frame_arr = np.zeros((Y_LENGTH, X_LENGTH))

def get_absolute_values():
    return min(raw_min), max(raw_max), np.mean(raw_mean)


def process_telemetry(data, sensor_number):
    global raw_min, raw_max, raw_mean
    raw_min[sensor_number] = (data[0] + 256 * data[1]) / 100
    raw_max[sensor_number] = (data[3] + 256 * data[4]) / 100
    raw_mean[sensor_number] = (data[6] + 256 * data[7]) / 100
    # print "telemetry values: ", raw_min, raw_max, raw_mean


def get_actual_temperature(raw_value, arr_max, arr_min, sensor_number):
    temp = (raw_max[sensor_number] - raw_min[sensor_number]) * (raw_value / (arr_max - arr_min)) + raw_min[sensor_number]
    return temp


def process_frame(raw_frame):
    if len(raw_frame) < 70:
        return

    # convert to bytes
    bytes_matrix = np.array([raw_frame[49:64],
                             raw_frame[33:48],
                             raw_frame[17:32],
                             raw_frame[1:16]])
    sensor_number = raw_frame[0] - 1 # sensors are numbered from 1 to 3, must subtract 1
    process_telemetry(np.array(raw_frame[65:]), sensor_number)
    arr_max = bytes_matrix.max()
    arr_min = bytes_matrix.min()

    for j in range(0, 4):
        y_coord = j + SENSOR_POSITIONS[sensor_number]
        for i in range(0, X_LENGTH):
            temp = get_actual_temperature(bytes_matrix[j][i], arr_max, arr_min, sensor_number)
            frame_arr[y_coord][i] = temp
    return frame_arr
