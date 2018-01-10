#!/usr/bin/python

### logging config
import logging
from logging.handlers import RotatingFileHandler

import Constants
from analysis.AnalysisProcess import AnalysisProcess

formatter = logging.Formatter("%(levelname)s [%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s")
LOGFILE = 'logs.log'
my_handler = RotatingFileHandler(LOGFILE, mode='a', maxBytes=1*1024*1024, backupCount=1, encoding=None, delay=0)
my_handler.setFormatter(formatter)
my_handler.setLevel(logging.INFO)
app_log = logging.getLogger('') #using default logger
app_log.addHandler(my_handler)
app_log.setLevel(logging.INFO)
### end logging config

import argparse
import psutil
import time
import os

from DetectSerialPorts import serial_ports
from Serial_reader import Serial_reader
from WebSocketConnection import WebSocketConnection
from multiprocessing import Process, Pipe
from Constants import HIGH_PRIORITY

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
    parser.add_argument(
        '-du', '--debug-url',
        help="use debug_url to connect defined on Constants.py",
        action="store_const", dest="Constants.URL", const=Constants.URL_DEBUG,
    )


    args = parser.parse_args()
    # logging.basicConfig(filename='logs.log', format=formatter, level=args.loglevel)
    return args



def main():
    args = define_args_and_log()
    port = serial_ports()[0]
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
            logging.warn("try to reconnect in 5 seconds")
            time.sleep(5)
    except KeyboardInterrupt or RuntimeError as e:
        usb_serial.close()
        exit(1)  # exit with error (it's supose to run forever)




if __name__ == '__main__':
    main()
