import Gui
import os
import argparse
import logging

from Camera import Camera
from Constants import *
from DetectSerialPorts import serial_ports
from ui.MainWindow import run_ui

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
        '-n', '--no-gui',
        help="Be verbose",
        action="store_const", dest="gui", const=False, default=True
    )
    args = parser.parse_args()
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT, level=args.loglevel)
    return args



def main():
    args = define_args_and_log()
    if args.gui:
        run_ui()
    else:
        print "no gui mode"
        cam = Camera(serial_ports()[0])

if __name__ == '__main__':
    main()
