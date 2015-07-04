from __future__ import absolute_import, unicode_literals

import logging

from serial import serial_for_url

from .connection import Connection
from .connection import SERIAL_BAUDRATE

logger = logging.getLogger(__name__)


class SerialConnection(Connection):

    def __init__(self, url, timeout=None):
        self.__serial = serial_for_url(url, SERIAL_BAUDRATE, timeout=timeout)

    def send(self, data):
        self.__serial.write(b'"')
        self.__serial.write(data)
        self.__serial.write(b'$')
        self.__serial.flush()

    def recv(self, bufsize):
        data = bytearray()
        while len(data) <= bufsize:
            c = self.__serial.read()
            logger.debug('serial read %r', c)
            if not c:
                break  # TODO: timeout?
            if c == b'$':
                break
            data.extend(c)
        return bytes(data)

    def close(self):
        self.__serial.close()
