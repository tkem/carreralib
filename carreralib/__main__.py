import argparse
import contextlib
import logging

from . import ControlUnit

parser = argparse.ArgumentParser()
parser.add_argument('address', metavar='ADDRESS')
parser.add_argument('-c', '--command', nargs='*')
parser.add_argument('-r', '--rawdata', nargs='*')
parser.add_argument('-l', '--listen', action='store_true')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARN)

with contextlib.closing(ControlUnit(args.address, timeout=2.0)) as cu:
    print('CU version: %s' % cu.version())
    for data in (args.rawdata or []):
        print('%s reponse: %s' % (data, cu.request(data.encode('ascii'))))
    for cmd in (args.command or []):
        print('%s reponse: %s' % (cmd, cu.command(*map(int, cmd.split()))))
    if args.listen:
        last = None
        while True:
            status = cu.status()
            if args.verbose or status != last:
                print(repr(status))
            last = status
