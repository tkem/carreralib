import argparse
import contextlib
import curses
import errno
import logging
import select
import time

from . import ControlUnit


def posgetter(driver):
    return (-driver.laps, driver.time)


def formattime(time, longfmt=False):
    if time is None:
        return "n/a"
    s = time // 1000
    ms = time % 1000

    if not longfmt:
        return "%d.%03d" % (s, ms)
    elif s < 3600:
        return "%d:%02d.%03d" % (s // 60, s % 60, ms)
    else:
        return "%d:%02d:%02d.%03d" % (s // 3600, (s // 60) % 60, s % 60, ms)


class RMS(object):

    HEADER = "Pos No         Time  Lap time  Best lap Laps Pit Fuel"
    FORMAT1 = "%s%s" % (
        "{pos:<4}#{car:<2}{time:>12}{laptime:>10}{bestlap:>10}",
        "{laps:>5}{pits:>4}{fuel:>5.0%}",
    )
    FORMAT2 = "%s%s" % (
        "{pos:<4}#{car:<2}{time:>12}{laptime:>10}{bestlap:>10}",
        "{laps:>5} n/a  n/a",
    )
    FOOTER1 = " * * * * *  SPACE to start/pause, ESC for pace car"
    FOOTER2 = " [R]eset, [S]peed, [B]rake, [F]uel, [C]ode, [Q]uit"

    # CU reports zero fuel for all cars unless pit lane adapter is connected
    # FUEL_MASK = ControlUnit.Status.FUEL_MODE | ControlUnit.Status.REAL_MODE
    FUEL_MASK = ControlUnit.Status.PIT_LANE_MODE

    class Driver(object):
        def __init__(self, num):
            self.num = num
            self.time = None
            self.laptime = None
            self.bestlap = None
            self.laps = 0
            self.pits = 0
            self.fuel = 0
            self.pit = False

        def newlap(self, timer):
            if self.time is not None:
                self.laptime = timer.timestamp - self.time
                if self.bestlap is None or self.laptime < self.bestlap:
                    self.bestlap = self.laptime
                self.laps += 1
            self.time = timer.timestamp

    def __init__(self, cu, window):
        self.cu = cu
        self.window = window
        self.titleattr = curses.A_STANDOUT
        self.lightattr = curses.color_pair(1)
        self.reset()

    def reset(self):
        self.drivers = [self.Driver(num) for num in range(1, 9)]
        self.maxlaps = 0
        self.start = None
        # discard remaining timer messages
        status = self.cu.request()
        while not isinstance(status, ControlUnit.Status):
            status = self.cu.request()
        self.status = status
        # reset cu timer
        self.cu.reset()
        # reset position tower
        self.cu.clrpos()

    def run(self):
        self.window.nodelay(1)
        last = None
        while True:
            try:
                self.update()
                c = self.window.getch()
                if c == ord("q"):
                    break
                elif c == ord("r"):
                    self.reset()
                elif c == ord(" "):
                    self.cu.start()
                elif c == 27:  # ESC
                    self.cu.request(ControlUnit.PACE_CAR_KEY)
                elif c == ord("s"):
                    self.cu.request(ControlUnit.SPEED_KEY)
                elif c == ord("b"):
                    self.cu.request(ControlUnit.BRAKE_KEY)
                elif c == ord("f"):
                    self.cu.request(ControlUnit.FUEL_KEY)
                elif c == ord("c"):
                    self.cu.request(ControlUnit.CODE_KEY)
                data = self.cu.request()
                # prevent counting duplicate laps
                if data == last:
                    continue
                elif isinstance(data, ControlUnit.Status):
                    self.handle_status(data)
                elif isinstance(data, ControlUnit.Timer):
                    self.handle_timer(data)
                else:
                    logging.warn("Unknown data from CU: " + data)
                last = data
            except select.error:
                pass
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise

    def handle_status(self, status):
        for driver, fuel in zip(self.drivers, status.fuel):
            driver.fuel = fuel
        for driver, pit in zip(self.drivers, status.pit):
            if pit and not driver.pit:
                driver.pits += 1
            driver.pit = pit
        self.status = status

    def handle_timer(self, timer):
        driver = self.drivers[timer.address]
        driver.newlap(timer)
        if self.maxlaps < driver.laps:
            self.maxlaps = driver.laps
            # position tower only handles 250 laps
            self.cu.setlap(self.maxlaps % 250)
        if self.start is None:
            self.start = timer.timestamp

    def update(self, blink=lambda: (time.time() * 2) % 2 == 0):
        window = self.window
        window.erase()
        nlines, ncols = window.getmaxyx()
        window.addnstr(0, 0, self.HEADER.ljust(ncols), ncols, self.titleattr)
        window.addnstr(nlines - 2, 0, self.FOOTER1, ncols - 1)
        window.addnstr(nlines - 1, 0, self.FOOTER2, ncols - 1)

        start = self.status.start
        if start == 0 or start == 7:
            pass
        elif start == 1:
            window.chgat(nlines - 2, 0, 2 * 5, self.lightattr)
        elif start < 7:
            window.chgat(nlines - 2, 0, 2 * (start - 1), self.lightattr)
        elif int(time.time() * 2) % 2 == 0:  # A_BLINK may not be supported
            window.chgat(nlines - 2, 0, 2 * 5, self.lightattr)

        drivers = [driver for driver in self.drivers if driver.time]
        for pos, driver in enumerate(sorted(drivers, key=posgetter), start=1):
            if pos == 1:
                leader = driver
                t = formattime(driver.time - self.start, True)
            elif driver.laps == leader.laps:
                t = "+%ss" % formattime(driver.time - leader.time)
            else:
                gap = leader.laps - driver.laps
                t = "+%d Lap%s" % (gap, "s" if gap != 1 else "")
            if (self.status.mode & self.FUEL_MASK) != 0:
                text = self.FORMAT1.format(
                    pos=pos,
                    car=driver.num,
                    time=t,
                    laps=driver.laps,
                    laptime=formattime(driver.laptime),
                    bestlap=formattime(driver.bestlap),
                    fuel=driver.fuel / 15.0,
                    pits=driver.pits,
                )
            else:
                text = self.FORMAT2.format(
                    pos=pos,
                    car=driver.num,
                    time=t,
                    laps=driver.laps,
                    laptime=formattime(driver.laptime),
                    bestlap=formattime(driver.bestlap),
                )
            window.addnstr(pos, 0, text, ncols)
        window.refresh()


parser = argparse.ArgumentParser(prog="python -m carreralib")
parser.add_argument(
    "device",
    metavar="DEVICE",
    nargs="?",
    help="the Control Unit device, e.g. a serial port or MAC address",
)
parser.add_argument(
    "-l", "--logfile", default="carreralib.log", help="where to write log messages"
)
parser.add_argument(
    "-t",
    "--timeout",
    default=1.0,
    type=float,
    help="maximum time in seconds to wait for Control Unit",
)
parser.add_argument(
    "-v", "--verbose", action="store_true", help="write more log messages"
)
args = parser.parse_args()

logging.basicConfig(
    level=logging.DEBUG if args.verbose else logging.WARN,
    filename=args.logfile,
    format="%(asctime)s: %(message)s",
)

if args.device is None:
    from . import connection

    parser.print_help()
    print("\ndevices:")
    nfound = 0
    for device, info in connection.scan():
        print("  %s\t%s" % (device, info))
        nfound += 1
    if not nfound:
        print("  none found")
    quit()

with contextlib.closing(ControlUnit(args.device, timeout=args.timeout)) as cu:
    print("CU version %s" % cu.version())

    def run(win):
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        rms = RMS(cu, win)
        rms.run()

    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass
