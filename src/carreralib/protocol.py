import re


class ProtocolError(Exception):
    """The base class of all protocol exceptions."""

    pass


class ChecksumError(Exception):
    """Raised when a checksum is wrong."""

    pass


def chksum(buf, offset=0, size=None):
    """Compute the protocol checksum for the buffer `buf`."""
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
    return sum(memoryview(buf[offset : offset + size]).tolist()) & 0x0F


def pack(fmt, *args):
    """Return a bytes object containing the arguments packed according to
    the format string `fmt.`

    """
    buf = bytearray()
    argiter = iter(args)
    for match in re.finditer(_FORMAT_RE, fmt):
        count, conv = match.groups()
        if count is None:
            count = 1
        else:
            count = int(count)
        if conv in _PACK_FORMATS:
            _PACK_FORMATS[conv](buf, argiter, count)
        else:
            raise ValueError("bad character in pack format")
    # TODO: check all args used
    return bytes(buf)


def unpack(fmt, buf):
    """Unpack from the buffer `buf` according to the format string `fmt`."""
    offset = 0
    result = []
    values = memoryview(buf).tolist()
    for match in re.finditer(_FORMAT_RE, fmt):
        count, conv = match.groups()
        if count is None:
            count = 1
        else:
            count = int(count)
        if conv in _UNPACK_FORMATS:
            offset += _UNPACK_FORMATS[conv](result, buf, values, offset, count)
        else:
            raise ValueError("bad character in unpack format")
    # TODO: check all buf used
    return tuple(result)


def _pack_B(buf, args, count, base=ord("0")):
    for _ in range(count):
        arg = next(args)
        if arg < 0 or arg > 0xFF:
            raise ValueError("'B' format argument out of range")
        buf.append(base + (arg & 0xF))
        buf.append(base + (arg >> 4))


def _pack_C(buf, args, offset, base=ord("0")):
    buf.append(base + chksum(buf, offset, len(buf) - offset))


def _pack_c(buf, args, count):
    for _ in range(count):
        arg = next(args)
        if not isinstance(arg, bytes) or len(arg) != 1:
            raise ValueError("'c' format requires a bytes object of length 1")
        buf.append(arg[0])


def _pack_I(buf, args, count, base=ord("0")):
    for _ in range(count):
        arg = next(args)
        if arg < 0 or arg > 0xFFFFFFFF:
            raise ValueError("'I' format argument out of range")
        buf.append(base + ((arg >> 24) & 0xF))
        buf.append(base + ((arg >> 28) & 0xF))
        buf.append(base + ((arg >> 16) & 0xF))
        buf.append(base + ((arg >> 20) & 0xF))
        buf.append(base + ((arg >> 8) & 0xF))
        buf.append(base + ((arg >> 12) & 0xF))
        buf.append(base + ((arg >> 0) & 0xF))
        buf.append(base + ((arg >> 4) & 0xF))


def _pack_s(buf, args, count, base=ord("0")):
    arg = next(args)
    if not isinstance(arg, bytes):
        raise ValueError("'s' format requires a bytes object")
    buf.extend(arg.ljust(count, base.to_bytes(1, byteorder="little"))[:count])


def _pack_x(buf, args, count, base=ord("0")):
    for _ in range(count):
        buf.append(base)


def _pack_Y(buf, args, count, base=ord("0")):
    for _ in range(count):
        arg = next(args)
        if arg < 0 or arg > 0xF:
            raise ValueError("'Y' format argument out of range")
        buf.append(base + arg)


def _unpack_B(result, buf, values, offset, count):
    for i in range(count):
        b = values[offset + i * 2] & 0x0F
        b |= (values[offset + i * 2 + 1] & 0x0F) << 4
        result.append(b)
    return count * 2


def _unpack_C(result, buf, values, offset, count):
    c = chksum(buf, count, offset - count)
    if values[offset] & 0xF != c:
        raise ChecksumError()
    return 1


def _unpack_c(result, buf, values, offset, count):
    for i in range(count):
        result.append(buf[offset + i : offset + i + 1])
    return count


def _unpack_I(result, buf, values, offset, count):
    for _ in range(count):
        n = (values[offset + 0] & 0x0F) << 24
        n |= (values[offset + 1] & 0x0F) << 28
        n |= (values[offset + 2] & 0x0F) << 16
        n |= (values[offset + 3] & 0x0F) << 20
        n |= (values[offset + 4] & 0x0F) << 8
        n |= (values[offset + 5] & 0x0F) << 12
        n |= (values[offset + 6] & 0x0F) << 0
        n |= (values[offset + 7] & 0x0F) << 4
        result.append(n)
    return count * 8


def _unpack_s(result, buf, values, offset, count):
    result.append(buf[offset : offset + count])
    return count


def _unpack_x(result, buf, values, offset, count):
    return count


def _unpack_Y(result, buf, values, offset, count):
    for i in range(count):
        result.append(values[offset + i] & 0xF)
    return count


_FORMAT_RE = re.compile(r"\s*([1-9]\d*|0)?(.)\s*")

_PACK_FORMATS = {
    "B": _pack_B,
    "C": _pack_C,
    "c": _pack_c,
    "I": _pack_I,
    "s": _pack_s,
    "x": _pack_x,
    "Y": _pack_Y,
}

_UNPACK_FORMATS = {
    "B": _unpack_B,
    "C": _unpack_C,
    "c": _unpack_c,
    "I": _unpack_I,
    "s": _unpack_s,
    "x": _unpack_x,
    "Y": _unpack_Y,
}
