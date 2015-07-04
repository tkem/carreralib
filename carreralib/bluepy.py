from __future__ import absolute_import, unicode_literals

import logging

from bluepy import btle

from .connection import BLE_OUTPUT_UUID, BLE_SERVICE_UUID
from .connection import Connection

logger = logging.getLogger(__name__)


class BluepyConnection(Connection):

    class Delegate(btle.DefaultDelegate):

        def handleNotification(self, handle, data):
            logger.debug('notification[%s]: %s', handle, data)
            self.data = data

    def __init__(self, address, timeout=None):
        self.__delegate = self.Delegate()
        self.__peripheral = btle.Peripheral(address, btle.ADDR_TYPE_RANDOM)
        self.__peripheral.setDelegate(self.__delegate)
        # FIXME: hard-coded handle 0x000f, should be characteristic UUID 2902
        self.__peripheral.writeCharacteristic(0x000f, b'\x03', False)
        service = self.__peripheral.getServiceByUUID(BLE_SERVICE_UUID)
        self.__output = service.getCharacteristics(BLE_OUTPUT_UUID)[0]
        self.__timeout = timeout

    def send(self, data):
        self.__output.write(data)

    def recv(self, bufsize):
        if self.__peripheral.waitForNotifications(self.__timeout):
            return self.__delegate.data
        else:
            raise Exception('Bluetooth timeout')

    def close(self):
        self.__peripheral.disconnect()
