#!/usr/bin/python

### logging config
import logging
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter("%(levelname)s [%(asctime)s %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s")
LOGFILE = 'logs.log'
my_handler = RotatingFileHandler(LOGFILE, mode='a', maxBytes=1*1024*1024, backupCount=1, encoding=None, delay=0)
my_handler.setFormatter(formatter)
app_log = logging.getLogger('') #using default logger
app_log.addHandler(my_handler)
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

    args = parser.parse_args()
    # logging.basicConfig(filename='logs.log', format=formatter, level=args.loglevel)
    return args



def main():
    args = define_args_and_log()
    port = serial_ports()[0]
    # the different process use a pipe to talk each other
    web_pipe, serial_pipe = Pipe()

    # serial runs its own process
    usb_serial = Serial_reader(serial_pipe, port)
    websocket = WebSocketConnection(web_pipe)

    def run_websocket():
        while usb_serial.is_open:
            websocket.run_forever()
            logging.warn("try to reconnect in 5")
            time.sleep(5)

    # give low priority to this process
    psutil.Process(os.getpid()).nice(HIGH_PRIORITY)

    try:
        run_websocket()
    except KeyboardInterrupt or RuntimeError as e:
        usb_serial.close()
        exit(1)  # exit with error (it's supose to run forever)




if __name__ == '__main__':
    main()
