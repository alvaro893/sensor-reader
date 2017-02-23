from HighCamera import HighCamera
from Utils import serial_ports, define_args_and_log
from lowCamera import LowCamera
from ui.MainWindow import run_ui

__author__ = 'Alvaro'


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
