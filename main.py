#!/usr/bin/python
import argparse
import logging

import time

from DetectSerialPorts import serial_ports
from Serial_reader import Serial_reader
from WebSocketConnection import WebSocketConnection

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
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT, level=args.loglevel)
    return args



def main():
    args = define_args_and_log()
    print "no gui mode"
    port = serial_ports()[0]

    websocket = WebSocketConnection()
    serial = Serial_reader(websocket.send_data, port)
    websocket.set_callback(serial.write)

    while(True):
        websocket.ws.run_forever()
        logging.warn("try to reconnect in 5")
        time.sleep(5)

    exit(1)  # exit with error


if __name__ == '__main__':
    main()
