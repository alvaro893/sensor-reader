import json

import logging

AUTHOR = 'Alvaro'
__author__ = AUTHOR

URL_DEBUG = "ws://localhost:8080"
CAMERA_PATH = "/camera"
CLIENT_PATH = "/client"
try:
    with open(".env.json") as f:
        data = json.load(f)
        PASS = data.get("WS_PASSWORD") or "0"
        WS_URL = data.get("URL") or "ws://cloudwebsocket2-ir-cloud.espoo-apps.ilab.cloud"
except IOError:
    logging.error("no .env file")

PARAMETERS = "?pass=%s" % PASS
PORT_LINUX = '/dev/ttyACM0', '/dev/ttyACM1'
PORT_WINDOWS = 'COM4', 'COM5'
INITIAL_SEQUENCE = b'\xff\xff\xff'
BAUD_SPEED = 115200

WINDOWS = 'nt'
print "using", WS_URL