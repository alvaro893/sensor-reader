from __future__ import division
import SerialCommunication as serial
import Analisys
import logging as log
import HttpConnection
import numpy as np

__author__ = 'Alvaro'
raw_min = None
raw_max = None
raw_mean = None
x_length = 15
y_length = 12
sensor_pos = (4, 0, 8)
arr_to_plot = np.zeros((y_length, x_length), dtype=np.uint8)
network_thread = HttpConnection.NetworkThread()
analysis_thread = Analisys.AsyncAnalysis(arr_to_plot)
buff = bytearray()


def process_telemetry(data):
    global raw_min, raw_max, raw_mean
    raw_min = (data[0] + 256 * data[1]) / 100
    raw_max = (data[3] + 256 * data[4]) / 100
    raw_mean = (data[6] + 256 * data[7]) / 100
    # print "telemetry values: ", raw_min, raw_max, raw_mean


def get_actual_temperature(raw_value, arr_max, arr_min):
    temp = (raw_max - raw_min) * (raw_value / (arr_max - arr_min)) + raw_min
    return temp


def process_line(frame):
    if len(frame) < 70:
        return

    global buff
    buff += frame
    if (len(buff) > 2048):
        network_thread.add_to_queue(buff)
        buff = bytearray()

    # conver to bytes
    bytes_matrix = np.array([frame[49:64],
                             frame[33:48],
                             frame[17:32],
                             frame[1:16]])
    sensor_number = frame[0]  # from 1 to 3, must subtract 1 in x_coord

    process_telemetry(np.array(frame[65:]))
    arr_max = bytes_matrix.max()
    arr_min = bytes_matrix.min()

    # print "raw data:", bytes_matrix
    # print "sensor: ", sensor_number
    # print "min:", arr_min, "max:", arr_max

    for j in range(0, 4):
        y_coord = j + sensor_pos[sensor_number - 1]
        for i in range(0, x_length):
            temp = get_actual_temperature(bytes_matrix[j][i], arr_max, arr_min)
            arr_to_plot[y_coord][i] = temp

    analysis_thread.put_arr_in_queue(arr_to_plot)
    log.debug("queue size:%d", analysis_thread.queue.qsize())


serial.start(process_line)  # this blocks

network_thread.stop
analysis_thread.stop
