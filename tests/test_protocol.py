from __future__ import unicode_literals

import unittest

from carreralib.protocol import chksum, pack, unpack


class ProtocolTest(unittest.TestCase):
    def test_chksum(self):
        for args, res in (
            ([b""], 0),
            ([b"0"], 0),
            ([b"1"], 1),
            ([b"5321"], 0xB),
            ([b"5321", 0], 0xB),
            ([b":5321", 1], 0xB),
            ([b"5321", 0, 4], 0xB),
            ([b"5321:", 0, 4], 0xB),
            ([b":5321", 1, 4], 0xB),
            ([b":5321:", 1, 4], 0xB),
            ([b"6091"], 0),
        ):
            self.assertEqual(chksum(*args), res)

    def test_pack(self):
        for fmt, args, res in (
            ("cBYYC", [b"J", 6, 9, 1], b"J60910"),
            ("cBYYC", [b"J", 6 | (5 << 5), 4, 1], b"J6:415"),
        ):
            self.assertEqual(pack(fmt, *args), res)

    def test_unpack(self):
        for fmt, buf, res in (
            ("c4sC", b"05321;", (b"0", b"5321")),
            ("cBYYC", b"J60910", (b"J", 6, 9, 1)),
            ("cBYYC", b"J6:415", (b"J", 6 | (5 << 5), 4, 1)),
            ("cYIYC", b"?2003037?>1=", (b"?", 2, 226287, 1)),
            ("cYIYC", b"?20030:9211<", (b"?", 2, 236050, 1)),
            ("cYIYC", b"?200301<?618", (b"?", 2, 246127, 1)),
            ("x8YC", b":01234500?", (0, 1, 2, 3, 4, 5, 0, 0)),
        ):
            self.assertEqual(unpack(fmt, buf), res)
