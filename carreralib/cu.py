from __future__ import absolute_import, division, unicode_literals

import logging

from collections import namedtuple

from . import connection
from . import protocol

logger = logging.getLogger(__name__)


class ControlUnit(object):
    """Interface to a Carrera Digital 124/132 Control Unit."""

    class Status(namedtuple('Status', 'fuel start mode pit')):

        __slots__ = ()

        MODE_FUEL = 1
        MODE_REAL = 2
        MODE_PIT_LANE = 4
        MODE_LAP_COUNTER = 8

    class Timer(namedtuple('Timer', 'address timestamp sector')):
        pass

    def __init__(self, device, **kwargs):
        if isinstance(device, connection.Connection):
            self.__connection = device
        else:
            logger.debug('Connecting to %s', device)
            self.__connection = connection.open(device, **kwargs)
            logger.debug('Connection established')

    def close(self):
        """Close the connection to the CU."""
        logger.debug('Closing connection')
        self.__connection.close()

    def clrpos(self):
        """Clear all position information."""
        self.__setword(6, 0, 9)

    def poll(self):
        """Poll CU for lap times or status information."""
        data = self.request(b'?')
        if data.startswith(b'?:'):
            parts = protocol.unpack('2x8YYYBYC', data)
            fuel, start, mode = parts[:8], parts[9], parts[10]
            pit = (parts[11] & (1 << n) != 0 for n in range(8))
            return ControlUnit.Status(fuel, start, mode, pit)
        else:
            return ControlUnit.Timer(protocol.unpack('xYIYC', data))

    def reset(self):
        """Reset the Control Unit's timer."""
        self.__request(b'=10')

    def setbrake(self, address, value):
        """Set the brake value for controller address."""
        self.__setword(1, address, value, repeat=2)

    def setfuel(self, address, value):
        """Set the fuel value for controller address."""
        self.__setword(2, address, value, repeat=2)

    def setlap(self, value):
        """Set the current lap."""
        if value < 0 or value > 255:
            raise ValueError('Lap value out of range')
        self.setlap_hi(value >> 4)
        self.setlap_lo(value & 0xf)

    def setlap_hi(self, value):
        """Set the high nibble of the current lap."""
        self.__setword(17, 7, value)

    def setlap_lo(self, value):
        """Set the low nibble of the current lap."""
        self.__setword(18, 7, value)

    def setpos(self, address, position):
        """Set the current position for controller address."""
        if position < 1 or position > 8:
            raise ValueError('Position out of range')
        self.__setword(6, address, position)

    def setspeed(self, address, value):
        """Set the speed value for controller address."""
        self.__setword(0, address, value, repeat=2)

    def start(self):
        """Initiate start sequence."""
        self.__request(b'T2')

    def version(self):
        """Retrieve CU version."""
        return str(protocol.unpack('x4sC', self.__request(b'0'))[0])

    def __request(self, buf, maxlength=None):
        logger.debug('Sending message %r', buf)
        self.connection.send(buf)
        while True:
            res = self.__connection.recv(maxlength)
            if res.startswith(buf[0:1]):
                break
            else:
                logger.warn('Received unexpected message %r', res)
        logger.debug('Received message %r', res)
        return res

    def __setword(self, word, address, value, repeat=1):
        if word < 0 or word > 31:
            raise ValueError('Command word out of range')
        if address < 0 or address > 7:
            raise ValueError('Address out of range')
        if value < 0 or value > 15:
            raise ValueError('Value out of range')
        if repeat < 1 or repeat > 15:
            raise ValueError('Repeat count out of range')
        buf = protocol.pack('cBYYC', word | (address << 5), value, repeat)
        return self.__request(buf)
