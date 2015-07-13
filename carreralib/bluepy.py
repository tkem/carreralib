from __future__ import absolute_import, division, unicode_literals

import collections

from bluepy import btle

from .connection import BufferTooShort, Connection, TimeoutError

SERVICE_UUID = '39df7777-b1b4-b90b-57f1-7144ae4e4a6a'
OUTPUT_UUID = '39df8888-b1b4-b90b-57f1-7144ae4e4a6a'
NOTIFY_UUID = '39df9999-b1b4-b90b-57f1-7144ae4e4a6a'


class BluepyDelegate(btle.DefaultDelegate):

    def __init__(self, sequence):
        self.__sequence = sequence

    def handleNotification(self, handle, data):
        # BLE notifications do not start with '?' but end with '$'...
        if data.endswith(b'$') and not data.startswith(b'?'):
            self.__sequence.append(b'?' + data[:-1])
        else:
            self.__sequence.append(data)


class BluepyConnection(Connection):

    def __init__(self, address, timeout=1.0):
        self.__data = collections.deque()
        self.__delegate = BluepyDelegate(self.__data)
        self.__peripheral = btle.Peripheral(address, btle.ADDR_TYPE_RANDOM)
        self.__peripheral.setDelegate(self.__delegate)
        # FIXME: hard-coded handle 0x000f, should be characteristic UUID 2902
        self.__peripheral.writeCharacteristic(0x000f, b'\x03', False)
        service = self.__peripheral.getServiceByUUID(SERVICE_UUID)
        self.__output = service.getCharacteristics(OUTPUT_UUID)[0]
        self.__timeout = timeout

    def close(self):
        self.__peripheral.disconnect()

    def recv(self, maxlength=None):
        if self.__delegate.data:
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
