import logging

import cv2
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from urlparse import urlparse
import socket, struct

def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))


def startup(cam):
    port = 8088
    class RequestHandler(BaseHTTPRequestHandler):
        # static variables
        camera = cam
        def do_GET(self):
            parsed_path = urlparse(self.path)
            message = '\n'.join([
                'CLIENT VALUES:',
                'client_address=%s (%s)' % (self.client_address,
                                            self.address_string()),
                'command=%s' % self.command,
                'path=%s' % self.path,
                'real path=%s' % parsed_path.path,
                'query=%s' % parsed_path.query,
                'request_version=%s' % self.request_version,
                '',
                'SERVER VALUES:',
                'server_version=%s' % self.server_version,
                'sys_version=%s' % self.sys_version,
                'protocol_version=%s' % self.protocol_version,
                '',
            ])

            logging.debug( message)
            if self.path.endswith('.mjpg'):
                self.send_response(200)
                self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--boundaryjpgxxx')
                self.end_headers()
                while True:
                    try:
                        time.sleep(0.1)
                        if not RequestHandler.camera:
                            continue
                        imgraw = RequestHandler.camera.last_frame
                        ret, img = cv2.imencode('.jpeg', imgraw)
                        # ret, img = cv2.imencode('.jpeg', np.random.randint(0, 255, (300, 300), dtype=np.uint8))
                        if not ret:
                            continue
                        self.wfile.write("--boundaryjpgxxx")
                        self.send_header('Content-type', 'image/jpg')
                        self.send_header('Content-length', str(img.shape[0]))
                        self.end_headers()
                        self.wfile.write(img.tobytes())

                        # jpg.save(self.wfile, 'JPEG')
                    except KeyboardInterrupt:
                        break
                return
            if self.path.endswith('mask.mjpg'):
                self.send_response(200)
                self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--boundaryjpgxxx')
                self.end_headers()
                while True:
                    try:
                        time.sleep(0.1)
                        if not RequestHandler.camera:
                            continue
                        imgraw = RequestHandler.camera.last_frame_mask
                        ret, img = cv2.imencode('.jpeg', imgraw)
                        # ret, img = cv2.imencode('.jpeg', np.random.randint(0, 255, (300, 300), dtype=np.uint8))
                        if not ret:
                            continue
                        self.wfile.write("--boundaryjpgxxx")
                        self.send_header('Content-type', 'image/jpg')
                        self.send_header('Content-length', str(img.shape[0]))
                        self.end_headers()
                        self.wfile.write(img.tobytes())

                        # jpg.save(self.wfile, 'JPEG')
                    except KeyboardInterrupt:
                        break
                return
            if self.path.endswith('.html'):
                ip_addr=get_default_gateway_linux()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write('<html><head></head><body>')
                self.wfile.write('<img src="http://127.0.0.1:' + str(port) + '/cam.mjpg"/>')
                self.wfile.write('</body></html>')
                return

    class VideoServer(ThreadingMixIn, HTTPServer):
        """ server in thread """

    try:
        server = VideoServer(('0.0.0.0', port), RequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        if server: server.socket.close()
