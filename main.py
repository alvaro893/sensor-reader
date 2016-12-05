import lowCamGui
import os
from Constants import *

__author__ = 'Alvaro'

def main():
    ports = PORT_LINUX
    if os.name == WINDOWS:
        ports = PORT_WINDOWS

    lowCamGui.start(ports)

main()