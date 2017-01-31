import json

import logging

AUTHOR = 'Alvaro'
__author__ = AUTHOR

# URL = "https://ir-sensor-cloud.appspot.com/"
URL = "http://server-ir-cloud.44fs.preview.openshiftapps.com/"
URL_DEBUG = "ws://localhost:8080"
WS_URL = "ws://cloudwebsocket2-ir-cloud.espoo-apps.ilab.cloud"
CAMERA_PATH = "/camera"
CLIENT_PATH = "/client"
PASS = '0'
try:
    with open(".env.json") as file:
        data = json.load(file)
        PASS = data["WS_PASSWORD"]
except Exception:
    logging.error("no .env file")

PARAMETERS = "?pass=%s" % PASS

PORT_LINUX = '/dev/ttyACM0', '/dev/ttyACM1'
PORT_WINDOWS = 'COM4', 'COM5'
INITIAL_SEQUENCE = b'\xff\xff\xff'
BAUD_SPEED = 115200

WINDOWS = 'nt'