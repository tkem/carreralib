from __future__ import absolute_import, division, unicode_literals

import collections
import logging

from bluepy import btle

from .connection import BufferTooShort, Connection, TimeoutError

SERVICE_UUID = '39df7777-b1b4-b90b-57f1-7144ae4e4a6a'
OUTPUT_UUID = '39df8888-b1b4-b90b-57f1-7144ae4e4a6a'
NOTIFY_UUID = '39df9999-b1b4-b90b-57f1-7144ae4e4a6a'

logger = logging.getLogger(__name__)


class BluepyDelegate(btle.DefaultDelegate):

    def __init__(self, sequence):
        self.__sequence = sequence

    def handleNotification(self, handle, data):
        logger.debug('Received notification message %r', data)
        # BLE notifications ending with '$' do not start with command letter
        if not data.endswith(b'$'):
            self.__sequence.append(data)
        elif len(data) == 6:
            self.__sequence.append(b'0' + data[:-1])
        else:
            self.__sequence.append(b'?' + data[:-1])


class BluepyConnection(Connection):

    def __init__(self, address, timeout=1.0):
        try:
            self.__peripheral = btle.Peripheral(address, btle.ADDR_TYPE_RANDOM)
        except Exception:
            self.__peripheral = None
            raise
        self.__data = collections.deque()
        self.__delegate = BluepyDelegate(self.__data)
        self.__peripheral.setDelegate(self.__delegate)
        # FIXME: hard-coded handle 0x000f, should be characteristic UUID 2902
        self.__peripheral.writeCharacteristic(0x000f, b'\x03', False)
        service = self.__peripheral.getServiceByUUID(SERVICE_UUID)
        self.__output = service.getCharacteristics(OUTPUT_UUID)[0]
        self.__timeout = timeout

    def __del__(self):
        self.close()

    def close(self):
        if self.__peripheral:
            try:
                self.__peripheral.disconnect()
            finally:
                self.__peripheral = None

    def recv(self, maxlength=None):
        if self.__data:
            buf = self.__data.popleft()
        elif self.__peripheral.waitForNotifications(self.__timeout):
            buf = self.__data.popleft()
        else:
            raise TimeoutError('Timeout waiting for Bluetooth notification')
        if maxlength is not None and maxlength < len(buf):
            raise BufferTooShort('Buffer too short for data received')
        return buf

    def send(self, buf, offset=0, size=None):
        n = len(buf)
        if offset < 0:
            raise ValueError("offset is negative")
        elif n < offset:
            raise ValueError("buffer length < offset")
        elif size is None:
            size = n - offset
        elif size < 0:
            raise ValueError("size is negative")
        elif offset + size > n:
            raise ValueError("buffer length < offset + size")
        self.__output.write(buf[offset:offset+size])
