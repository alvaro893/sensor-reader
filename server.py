import logging
import json
import cv2
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from urlparse import urlparse, parse_qs
import socket, errno, struct
import os
import Cache
import Raspberry_commands
from analysis import Images


def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

def int16_to_bytes(i):
    if i > 65535:
        return bytearray()
    n = int(i)
    lowByte = n & 0xff
    highByte = n >> 8
    return bytearray([highByte, lowByte])



def handleError(e):
    if isinstance(e.args, tuple):
        if e[0] == errno.EPIPE or e[0] == errno.ECONNRESET:
           # remote peer disconnected
           logging.info("client reading video feed disconnected");
        else:
           # determine and handle different error
           logging.error("unhandled socket error detected, errno is %d" % e[0])
    else:
           logging.error("unhandled socket error detected, %d" % e)

def startup(camera, serial_pipe):
    port = 8088
    class RequestHandler(BaseHTTPRequestHandler):
        # static variables
        _camera = camera
        _serial_pipe = serial_pipe

        def do_HEAD(self):
            self.send_response(200)

        def authorize(self):
            auth = self.headers.getheader('Authorization')
            if auth != 'Basic YWRtaW46bGV2aXRlemVyMjAxOA==': #admin:levitezer2018
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Basic realm=\"Unauthorized access forbidden\"')
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("\r\n")
                return False
            else:
                return True

        def handleBody(self):
            try:
                leng = int(self.headers['Content-Length'])
                content_type = str(self.headers['Content-Type'])

                if content_type.find('text/plain') == -1:
                    self.send_response(406)
                    return False
                if leng > 5:
                    self.send_response(411)
                    return False
                value = int(self.rfile.read(leng))
                self.send_response(200)
                return value
            except Exception as e:
                logging.warn(e.message)
                self.send_response(400)
                return False


        def do_PUT(self):
            if not self.authorize():
                return

            if(self.path == '/calibrate'):
                self.send_response(200)
                RequestHandler._serial_pipe.send('C')
            elif (self.path == '/sync'):
                self.send_response(200)
                RequestHandler._serial_pipe.send('S')
            elif (self.path == '/automin'):
                self.send_response(200)
                RequestHandler._serial_pipe.send('a')
            elif (self.path == '/automax'):
                self.send_response(200)
                RequestHandler._serial_pipe.send('A')
            elif (self.path == '/delay'):
                value = self.handleBody()
                if value:
                    RequestHandler._serial_pipe.send('U'+int16_to_bytes(value))

            elif (self.path == '/min'):
                value = self.handleBody()
                if value:
                    RequestHandler._serial_pipe.send('L'+int16_to_bytes(value))

            elif (self.path == '/max'):
                value = self.handleBody()
                if value:
                    RequestHandler._serial_pipe.send('H'+int16_to_bytes(value))

            elif (self.path == '/reboot'):
                self.send_response(200)
                Raspberry_commands.resetsensor()

            elif (self.path == '/update'):
                self.send_response(200)
                Raspberry_commands.update()

            else:
                self.send_response(404)

            self.end_headers()


        def do_GET(self):
            """process get requests"""

            if not self.authorize():
                return

            parsed_path = urlparse(self.path)
            parsed_query = parse_qs(parsed_path.query)


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
                try:
                    sizex = int(parsed_query['sizex'][0])
                    sizey = int(parsed_query['sizey'][0])
                except Exception:
                    sizex = 0;
                    sizey = 0
                try:
                    quality = int(parsed_query['quality'][0])
                except Exception:
                    quality = 0  # from 0 to 100 (the higher is the better). Default value is 95.


                old_frame_hash = 0
                if parsed_path.path == '/color.mjpg':
                    img_raw = RequestHandler._camera.last_frame_stream
                elif parsed_path.path == '/normalized.mjpg':
                    img_raw = RequestHandler._camera.normalized_frame_visible
                elif parsed_path.path == '/cam.mjpg':
                    img_raw = RequestHandler._camera.last_frame
                elif parsed_path.path == '/background.mjpg':
                    img_raw = RequestHandler._camera.bg_subscration_frame
                elif parsed_path.path == '/mask.mjpg':
                    img_raw = RequestHandler._camera.last_frame_mask
                elif parsed_path.path == '/heatmap.mjpg':
                    img_raw = RequestHandler._camera.masked_heatmap
                else:
                    self.send_response(404)
                    self.end_headers()
                    return

                self.send_response(200)
                self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--boundaryjpg')
                self.end_headers()
                while True:
                    # TODO: remove sleep ? we still need for performance, hash check is not enough...
                    time.sleep(0.005)
                    # skip until new frame
                    if RequestHandler._camera.last_frame_hash == old_frame_hash:
                        continue

                    try:
                        if not RequestHandler._camera:
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
                        self.wfile.write("--boundaryjpg")
                        self.wfile.write("\r\n") # always line feed after boundary
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', str(img.shape[0]))
                        self.end_headers()
                        self.wfile.write(img.tobytes())

                        old_frame_hash = RequestHandler._camera.last_frame_hash
                        # jpg.save(self.wfile, 'JPEG')

                    except socket.error as e:
                        handleError(e)
                        return #exit infinite loop

            elif self.path == '/telemetry':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                json.dump(RequestHandler._camera.telemetry, self.wfile)

            elif self.path == '/analysis':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                json.dump(Cache.analysis_data, self.wfile)

            elif self.path == '/colored_heatmap.png':
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                try:
                    ret, buf = Images.getBufferedImage(Images._colored_heatmap)
                    self.wfile.write(buf.tobytes())
                except Exception as e:
                    self.send_response(404)

            elif self.path == '/build.log':
                self.do_get_file('build.log')

            elif self.path == '/logs.log':
                self.do_get_file('logs.log')

            elif (self.path == '/load'):
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                text = Raspberry_commands.loadavg(self.wfile)

            else:
                self.send_response(404)

        def do_get_file(self,filename):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            if os.path.isfile(filename):
                with open(filename) as fp:
                    for line in fp:
                        self.wfile.write(line)
            else:
                self.wfile.write('no file "'+filename+'" found \n')

    class VideoServer(ThreadingMixIn, HTTPServer):
        """ server in thread """

    try:
        server = VideoServer(('0.0.0.0', port), RequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        if server: server.socket.close()
