from __future__ import absolute_import, division, unicode_literals

import logging
from collections import namedtuple

from . import connection
from . import protocol

logger = logging.getLogger(__name__)


class ControlUnit(object):
    """Interface to a Carrera Digital 124/132 Control Unit."""

    class Status(namedtuple('Status', 'fuel start mode pit display')):

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
        self.setword(6, 0, 9)

    def ignore(self, mask):
        """Ignore the controllers represented by bitmask `mask`."""
        self.request(protocol.pack('cBC', b':', mask))

    def request(self, buf=b'?', maxlength=None):
        """Send a message to the CU and wait for a response."""
        logger.debug('Sending message %r', buf)
        self.__connection.send(buf)
        while True:
            res = self.__connection.recv(maxlength)
            if res.startswith(buf[0:1]):
                break
            else:
                logger.warn('Received unexpected message %r', res)
        logger.debug('Received message %r', res)
        if res.startswith(b'?:'):
            # recent CU versions report two extra unknown bytes with '?:'
            try:
                parts = protocol.unpack('2x8YYYBYC', res)
            except protocol.ChecksumError:
                parts = protocol.unpack('2x8YYYBYxxC', res)
            fuel, (start, mode, pitmask, display) = parts[:8], parts[8:]
            pit = tuple(pitmask & (1 << n) != 0 for n in range(8))
            return ControlUnit.Status(fuel, start, mode, pit, display)
        elif res.startswith(b'?'):
            address, timestamp, sector = protocol.unpack('xYIYC', res)
            return ControlUnit.Timer(address - 1, timestamp, sector)
        else:
            return res

    def reset(self):
        """Reset the CU timer."""
        self.request(b'=10')

    def setbrake(self, address, value):
        """Set the brake value for controller `address`."""
        self.setword(1, address, value, repeat=2)

    def setfuel(self, address, value):
        """Set the fuel value for controller `address`."""
        self.setword(2, address, value, repeat=2)

    def setlap(self, value):
        """Set the current lap."""
        if value < 0 or value > 255:
            raise ValueError('Lap value out of range')
        self.setlap_hi(value >> 4)
        self.setlap_lo(value & 0xf)

    def setlap_hi(self, value):
        """Set the high nibble of the current lap."""
        self.setword(17, 7, value)

    def setlap_lo(self, value):
        """Set the low nibble of the current lap."""
        self.setword(18, 7, value)

    def setpos(self, address, position):
        """Set the current position for controller address."""
        if position < 1 or position > 8:
            raise ValueError('Position out of range')
        self.setword(6, address, position)

    def setspeed(self, address, value):
        """Set the speed value for controller address."""
        self.setword(0, address, value, repeat=2)

    def setword(self, word, address, value, repeat=1):
        if word < 0 or word > 31:
            raise ValueError('Command word out of range')
        if address < 0 or address > 7:
            raise ValueError('Address out of range')
        if value < 0 or value > 15:
            raise ValueError('Value out of range')
        if repeat < 1 or repeat > 15:
            raise ValueError('Repeat count out of range')
        buf = protocol.pack('cBYYC', b'J', word | address << 5, value, repeat)
        return self.request(buf)

    def start(self):
        """Initiate CU start sequence."""
        self.request(b'T2')

    def version(self):
        """Retrieve CU version."""
        return protocol.unpack('x4sC', self.request(b'0'))[0]
