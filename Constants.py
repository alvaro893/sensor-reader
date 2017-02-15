import json

import logging

AUTHOR = 'Alvaro'
__author__ = AUTHOR

# URL = "https://ir-sensor-cloud.appspot.com/"
URL_DEBUG = "ws://localhost:8080"
CAMERA_PATH = "/camera"
CLIENT_PATH = "/client"
try:
    with open(".env.json") as file:
        data = json.load(file)
        PASS = data.get("WS_PASSWORD") or "0"
        URL = data.get("URL") or "ws://cloudwebsocket2-ir-cloud.espoo-apps.ilab.cloud"
except Exception:
    logging.error("no .env.json file")
    exit(1)

PARAMETERS = "?pass=%s" % PASS

PORT_LINUX = '/dev/ttyACM0', '/dev/ttyACM1'
PORT_WINDOWS = 'COM4', 'COM5'
INITIAL_SEQUENCE = b'\xff\xff\xff'
BAUD_SPEED = 115200

WINDOWS = 'nt'

VERY_HIGH_PRIORITY = -10
HIGH_PRIORITY = -1