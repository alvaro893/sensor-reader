import argparse
import logging
from time import sleep

from DetectSerialPorts import serial_ports
from SerialCommunication import SerialCommunication
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
    serial = SerialCommunication(websocket.send_to_socket, port, get_raw_data_only=True)
    websocket.set_callback(serial.write_to_serial)

    while True:
       sleep(1000) # block this thread



if __name__ == '__main__':
    main()
