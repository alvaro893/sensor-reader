import argparse
import logging

from HighCamera import HighCamera
from Utils import serial_ports
from lowCamera import LowCamera
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
        help="only send data to cloud",
        action="store_const", dest="gui", const=False, default=True
    )

    parser.add_argument(
        '-l',
        help="select low resolution camera (only whit --no-gui)",
        action="store_const", dest="low_cam", const=True, default=False
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
        port = serial_ports()[0]
        if args.low_cam:
            cam = LowCamera(port, only_send_data=True)
        else:
            cam = HighCamera(port, only_send_data=True)

if __name__ == '__main__':
    main()
