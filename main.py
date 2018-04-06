#!/usr/bin/python

import logging
import socket
import sys
from logging.handlers import RotatingFileHandler

import Cache
import M2MApi
from MqttClient import instance as mqtt_client

from analysis.AnalysisProcess import AnalysisProcess

### logging to file and stdout
LOG_LEVEL = Cache.get_var("LOG_LEVEL")
formatter = logging.Formatter("%(levelname)s [%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s")
LOGFILE = 'logs.log'
file_handler = RotatingFileHandler(LOGFILE, mode='a', maxBytes=1 * 1024 * 1024, backupCount=1, encoding=None, delay=0)
file_handler.setFormatter(formatter)
file_handler.setLevel(LOG_LEVEL)
std_handler = logging.StreamHandler(sys.stdout)
std_handler.setLevel(LOG_LEVEL)
std_handler.setFormatter(formatter)
app_log = logging.getLogger('') #using default logger
app_log.addHandler(file_handler)
app_log.addHandler(std_handler)
app_log.setLevel(LOG_LEVEL)
### end logging config

import argparse
import psutil
import time
import os

from DetectSerialPorts import serial_ports
from Serial_reader import Serial_reader
from WebSocketConnection import WebSocketConnection
from multiprocessing import Pipe
from Cache import HIGH_PRIORITY

__author__ = 'Alvaro'


def define_args_and_log():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    # parser.add_argument(
    #     '-du', '--debug-url',
    #     help="use debug_url to connect defined on Constants.py",
    #     action="store_const", dest="Constants.URL", const=Constants.URL_DEBUG,
    # )


    args = parser.parse_args()
    # logging.basicConfig(filename='logs.log', format=formatter, level=args.loglevel)
    return args



def main():
    args = define_args_and_log()
    try:
        SECRET, TOKEN, USER = M2MApi.getCredentials()
        Cache.save_var(IMPACT_SECRET=SECRET, IMPACT_TOKEN=TOKEN, IMPACT_USER=USER)
    except Exception as e:
        logging.warning("Could not update Impact credentials: %s", e)


    try:
        port = serial_ports()[0]
        mqtt_client.start()
        mqtt_client.submit_configuration()
    except IndexError:
        logging.fatal("sensor not connected to port. Exiting...")
        exit(1)
    except socket.error as socketErr:
        logging.error("Could not connect to Impact: socket error message: %s", socketErr.strerror)

    # NOTE: each endpoint of a pipe can be only read by 1 process or thread, otherwise the data on the
    # pipe will be corrupted. That's why there is need of two pipes

    # pipe between network and serial processes
    net_pipe_A, net_pipe_B = Pipe()
    # pipe between serial and analysis
    analysis_pipe_A, analysis_pipe_B = Pipe()

    # serial runs its own process
    usb_serial = Serial_reader(net_pipe_B, analysis_pipe_B, port)

    # network and analysis processes
    websocket = WebSocketConnection(net_pipe_A)
    analysisProcess = AnalysisProcess(analysis_pipe_A)

    # give low priority to this process (websocket)
    try:
        psutil.Process(os.getpid()).nice(HIGH_PRIORITY)
    except psutil.AccessDenied as e:
        logging.error("do not have permission to change priority!")


    # Main loop
    try:
        while usb_serial.is_open:
            websocket.run_forever()
            logging.warn("trying to reconnect to websocket...")
            time.sleep(5)
    except KeyboardInterrupt or RuntimeError as e:
        usb_serial.close()
        exit(1)  # exit with error (it's supose to run forever)




if __name__ == '__main__':
    main()
