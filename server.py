import logging

import cv2
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from urlparse import urlparse, parse_qs
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
            parsed_query = parse_qs(parsed_path.query)
            try:
                sizex = int(parsed_query['sizex'][0])
                sizey = int(parsed_query['sizey'][0])
            except Exception:
                sizex = 0; sizey = 0
            try:
                quality = int(parsed_query['quality'][0])
            except Exception:
                quality = 0 # from 0 to 100 (the higher is the better). Default value is 95.

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
            if parsed_path.path.endswith('.mjpg'):
                if parsed_path.path == '/cam.mjpg':
                    img_raw = RequestHandler.camera.last_frame
                elif parsed_path.path == '/background.mjpg':
                    img_raw = RequestHandler.camera.bg_subscration_frame
                elif parsed_path.path == '/mask.mjpg':
                    img_raw = RequestHandler.camera.last_frame_mask
                elif parsed_path.path == '/heatmap.mjpg':
                    img_raw = RequestHandler.camera.masked_heatmap
                else:
                    self.send_response(404)
                    self.end_headers()
                    return

                self.send_response(200)
                self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--boundaryjpgxxx')
                self.end_headers()
                while True:
                    try:
                        time.sleep(0.1)
                        if not RequestHandler.camera:
                            continue
                        if quality == 0:
                            quality = 95
                        if sizex == 0 or sizey == 0:
                            ret, img = cv2.imencode('.jpeg', img_raw, [cv2.IMWRITE_JPEG_QUALITY, quality])
                        else:
                            resized_img = cv2.resize(img_raw, (sizex, sizey), interpolation=cv2.INTER_CUBIC)
                            ret, img = cv2.imencode('.jpeg', resized_img, [cv2.IMWRITE_JPEG_QUALITY, quality])
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
                    except socket.error as e:
                        logging.info("%s, %s, %s", e.strerror, e.errno)
                        break

                return
            elif self.path.endswith('.html'):
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
