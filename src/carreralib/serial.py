from serial import serial_for_url

from .connection import BufferTooShort, Connection, TimeoutError


class SerialConnection(Connection):

    __serial = None

    def __init__(self, url, timeout=None):
        self.__serial = serial_for_url(url, baudrate=19200, timeout=timeout)

    def close(self):
        if self.__serial:
            self.__serial.close()

    def recv(self, maxlength=None):
        buf = bytearray()
        while True:
            c = self.__serial.read()
            if not c:
                raise TimeoutError("Timeout waiting for serial data")
            elif c == b"$" or c == b"#":
                break
            elif maxlength is not None and maxlength <= len(buf):
                raise BufferTooShort("Buffer too short for data received")
            else:
                buf.extend(c)
        return bytes(buf)

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
        self.__serial.write(b'"')
        self.__serial.write(buf[offset : offset + size])
        self.__serial.write(b"$")
        self.__serial.flush()

    @classmethod
    def scan(_):
        from serial.tools.list_ports import comports

        return ((info.device, info.description) for info in comports())
