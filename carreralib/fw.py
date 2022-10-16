import argparse
import contextlib
import logging

from . import ControlUnit

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='python -m carreralib.fw')
    parser.add_argument('device', metavar='DEVICE')
    parser.add_argument('updatefile', metavar='FILE', nargs='?', default=None)
    parser.add_argument('-l', '--logfile', nargs='?', default='carreralib.log', const=None)
    parser.add_argument('-t', '--timeout', default=1.0, type=float)
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        filename=args.logfile,
                        format='%(asctime)s: %(message)s')

    with contextlib.closing(ControlUnit(args.device, timeout=args.timeout)) as cu:
        print('CU version %s' % cu.version().decode())

        if args.updatefile:
            cu.updatefw(args.updatefile)

