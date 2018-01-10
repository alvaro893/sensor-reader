import argparse
import glob
import sys

import logging
import serial

# Define miscellaneous functions

def int_to_bytes(n):
    s = '%x' % n
    if len(s) & 1:
        s = '0' + s
    return s.decode('hex')


def from_bytes_to_int(s):
    if type(s) != 'str':
        s = str(s)
    return int(s.encode('hex'), 16)


def descale(val, pmin, pmax):
    """
    :return: tuple with a value and the next
    """
    raw_val = val * (pmax - pmin) / 254 + pmin
    return raw_val >> 8, (raw_val & 0xff)+1


def scale(val, other, pmin, pmax):  # for consulting purposes
    raw = val << 8 | other
    return ((raw - pmin) * 254) / (pmax - pmin)


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(2,256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/ttyACM[0-9]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

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