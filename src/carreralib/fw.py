import argparse
import contextlib
import logging
import time

from . import ControlUnit

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="python -m carreralib.fw")
    parser.add_argument("device", metavar="DEVICE")
    parser.add_argument("file", metavar="FILE", nargs="?", default=None)
    parser.add_argument("-l", "--logfile", default="carreralib.log")
    parser.add_argument("-t", "--timeout", default=1.0, type=float)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        filename=args.logfile,
        format="%(asctime)s: %(message)s",
    )

    with contextlib.closing(ControlUnit(args.device, timeout=args.timeout)) as cu:
        print("CU version %s" % cu.version().decode())

        if args.file:
            with open(args.file) as f:
                # remove double quotes wrapping each line
                lines = [line.rstrip().replace('"', "") for line in f.readlines()]
                # skip empty lines
                lines = [line for line in lines if len(line)]
            if lines:
                print("Starting firmware update")
                cu.fwu_start()
                time.sleep(1.0)  # wait a little...
                for n, line in enumerate(lines):
                    # encode to bytes and write to CU
                    cu.fwu_write(line.encode())
                    # print progress
                    print("Writing firmware update block %d/%d" % (n + 1, len(lines)))
                time.sleep(1.0)  # wait some more...
                print("CU version %s" % cu.version().decode())
