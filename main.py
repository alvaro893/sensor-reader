import Gui
import os
import argparse
import logging
from Constants import *
from ui.MainWindow import run_ui

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
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT, level=args.loglevel)


def main():
    define_log_level()
    run_ui()

if __name__ == '__main__':
    main()
