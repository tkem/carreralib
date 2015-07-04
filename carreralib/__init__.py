"""Communicate with Carrera Digital 124/132 Control Unit"""

from __future__ import unicode_literals

from . import connection

__version__ = '0.1.0'


class ControlUnit(object):

    class Status(bytes):

        @property
        def fuel(self):
            return tuple(map(lambda x: ord(x) & 0xf, self[1:9]))

        @property
        def start(self):
            return ord(self[9]) & 0xf

        @property
        def mode(self):
            return ord(self[10]) & 0xf

        @property
        def pit(self):
            # TODO: set or array?
            return (ord(self[11]) & 0xf) | ((ord(self[12]) & 0xf) << 4)

        def __repr__(self):
            return '%s(fuel=%r, start=%d, mode=%d, pit=%r)' % (
                self.__class__.__name__,
                self.fuel, self.start, self.mode, self.pit
            )

    class Lap(bytes):

        @property
        def car(self):
            return ord(self[0]) & 0xf

        @property
        def time(self):
            lo = map(lambda x: ord(x) & 0xf, self[1:9:2])
            hi = map(lambda x: ord(x) & 0xf, self[2:9:2])
            time = 0
            for h, l in zip(hi, lo):
                time = time << 8
                time = time | (h << 4)
                time = time | l
            return time

        @property
        def timer(self):
            return ord(self[1]) & 0xf

        def __repr__(self):
            return '%s(car=%d, time=%d, timer=%d)' % (
                self.__class__.__name__,
                self.car, self.time, self.timer
            )

    def __init__(self, address, timeout=None):
        self.connection = connection.open(address, timeout)

    def reset(self):
        self.request(b'=10')

    def start(self):
        self.request(b'T2')  # TODO: checksum

    def status(self):
        response = self.request(b'?')
        if response.startswith(b'?'):
            # TODO: ble does not include '?'?
            response = response[1:]
        if response.startswith(b':'):
            return self.Status(response)
        else:
            return self.Lap(response)

    def version(self):
        # TODO: checksum?
        return str(self.request(b'0')[0:4])

    def setspeed(self, address, value):
        self.command(0, address, value, repeat=2)

    def setbrake(self, address, value):
        self.command(1, address, value, repeat=2)

    def setfuel(self, address, value):
        self.command(2, address, value, repeat=2)

    def setpos(self, address, position):
        self.command(6, address, position)

    def setlap(self, lap):
        self.command(17, 7, (lap >> 4) & 0x0f)
        self.command(18, 7, lap & 0x0f)

    # TODO: or clearpos? or clear()
    def clearlap(self):
        self.command(6, 0, 9)

    def close(self):
        self.connection.close()

    def request(self, data, bufsize=16 + 2):
        # TODO: clear input buffer?
        self.connection.send(data)
        resp = self.connection.recv(bufsize)
        if not resp:
            raise Exception('timeout')  # FIXME
        return resp

    def command(self, cmd, address, value, repeat=1):
        nibbles = [cmd & 0xf, (cmd >> 4) | (address << 1), value, repeat]
        nibbles.append(sum(nibbles) & 0x0f)
        data = b'J' + b''.join(map(lambda x: chr(x + 48), nibbles)) + b'$'
        return self.request(data)
