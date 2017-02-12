import thread
import logging
from threading import Thread
from serial import Serial, SerialException


class Serial_reader(Serial, Thread):
    """" This class read data from sensor in a Thread """

    def __init__(self, callback, port):
        Thread.__init__(self, name="SerialThread")
        Serial.__init__(self, port=port, baudrate=115200)
        self.callback = callback
        self.setDaemon(True)
        self.start()

    def _get_data(self):
        # necessary to block thread (in_waiting method doesn't block)
        one_byte = self.read(1)
        n_bytes = self.in_waiting
        return one_byte + self.read(n_bytes)

    def run(self):
        while self.is_open:
            try:
                data = self._get_data()
                thread.start_new_thread(self.callback, (data,))
            except SerialException as e:
                logging.error(e.message)
                break

    def write(self, data):
        if self.is_open:
            Serial.write(self, data)

    def stop(self):
        if self.is_open:
            Serial.close()
