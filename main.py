import Gui
import os
import argparse
import logging
from Constants import *

__author__ = 'Alvaro'


def define_log_level():
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
    logging.basicConfig(level=args.loglevel)


def define_ports():
    ports = PORT_LINUX
    if os.name == WINDOWS:
        ports = PORT_WINDOWS
    return ports


def main():
    define_log_level()
    Gui.start()

main()
