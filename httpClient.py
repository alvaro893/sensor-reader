import logging
from httplib import HTTPConnection, HTTPException
from threading import Thread

from Constants import URL, CAMERA_NAME, PORT


# timeout for each request will be 1 sec
from analysis import Images


def submitData(data, data_name):
    http = HTTPConnection(URL, PORT, timeout=2)
    try:
        http.request("POST", "/"+data_name+"?camera_name="+CAMERA_NAME, body=str(data), headers={"Content-Type":"text/plain"})
        # http.getresponse().read()
    except HTTPException as e:
        logging.error(e.message)
    finally:
        http.close()


def submitImageBuffer(imgName):
    http = HTTPConnection(URL, PORT, timeout=2)
    try:
        retval, buf = Images.getBufferedImage(imgName)
        if retval:
            http.request("POST", "/heatmap?camera_name=" + CAMERA_NAME, body=buf, headers={"Content-Type": "image/png"})
            # http.getresponse()
    except HTTPException as e:
        logging.error(e.message)
    finally:
        http.close()

