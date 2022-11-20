import argparse
import contextlib
import logging
import time

from . import ControlUnit

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="python -m carreralib.fw")
    parser.add_argument(
        "device",
        metavar="DEVICE",
        help="the Control Unit device, e.g. a serial port or MAC address",
    )
    parser.add_argument(
        "file",
        metavar="FILE",
        nargs="?",
        default=None,
        help="a Control Unit firmware update file",
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="force firmware update"
    )
    parser.add_argument(
        "-l", "--logfile", default="carreralib.log", help="where to write log messages"
    )
    parser.add_argument(
        "-t",
        "--timeout",
        default=5.0,
        type=float,
        help="maximum time in seconds to wait for Control Unit",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="write more log messages"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        filename=args.logfile,
        format="%(asctime)s: %(message)s",
    )

    with contextlib.closing(ControlUnit(args.device, timeout=args.timeout)) as cu:
        if not args.file or not args.force:
            print("CU version %s" % cu.version())

        if args.file:
            with open(args.file) as f:
                # remove double quotes wrapping each line
                lines = [line.rstrip().replace('"', "") for line in f.readlines()]
                # skip empty lines
                lines = [line for line in lines if len(line)]
            if lines:
                print("Starting firmware update")
                cu.fwu_start()
                time.sleep(2.0)  # wait for two seconds...
                for n, line in enumerate(lines):
                    # encode to bytes and write to CU
                    cu.fwu_write(line.encode())
                    # print progress
                    print("Writing firmware update block %d/%d" % (n + 1, len(lines)))
                print("Firmware update done")
