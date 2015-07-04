from __future__ import absolute_import, unicode_literals

import sys

BLE_SERVICE_UUID = '39df7777-b1b4-b90b-57f1-7144ae4e4a6a'

BLE_OUTPUT_UUID = '39df8888-b1b4-b90b-57f1-7144ae4e4a6a'

BLE_NOTIFY_UUID = '39df9999-b1b4-b90b-57f1-7144ae4e4a6a'

SERIAL_BAUDRATE = 19200


class Connection(object):

    def __init__(self, url, timeout=None):
        pass

    def send(self, data):
        raise NotImplementedError

    def recv(self, bufsize):
        raise NotImplementedError

    def close(self):
        pass


def open(url, timeout=None):
    if not isinstance(url, bytes):
        url = url.encode(sys.getfilesystemencoding())
    if len(url.split(b':')) == 6:
        from .bluepy import BluepyConnection
        return BluepyConnection(url, timeout)
    else:
        from .serial import SerialConnection
        return SerialConnection(url, timeout)
