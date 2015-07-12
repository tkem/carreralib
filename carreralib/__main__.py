from __future__ import unicode_literals

import argparse
import contextlib
import errno
import logging
import select
import time

from . import ControlUnit


def posgetter(driver):
    return (-len(driver.laps), driver.laps[-1].time)


def formattime(time, longfmt=False):
    s = time // 1000
    ms = time % 1000

    if not longfmt:
        return '%d.%03d' % (s, ms)
    elif s < 3600:
        return '%d:%02d.%03d' % (s // 60, s % 60, ms)
    else:
        return '%d:%02d:%02d.%03d' % (s // 3600, (s // 60) % 60, s % 60, ms)


class CursesRMS(object):

    HEADER = 'Pos No         Time  Lap time  Best lap Laps Pit Fuel'
    FORMAT = ('{pos:<4}#{car:<2}{time:>12}{laptime:>10}{bestlap:>10}' +
              '{laps:>5}{pits:>4}{fuel:>5.0%}')
    FOOTER = ' * * * * * Press space to start/pause, r for reset, q to quit'

    class Driver(object):
        def __init__(self, num):
            self.num = num
            self.fuel = 0
            self.laps = []
            self.pit = False
            self.pits = 0

        def laptime(self):
            if len(self.laps) > 1:
                return self.laps[-1].time - self.laps[-2].time
            else:
                return 0

        def bestlap(self):
            if len(self.laps) > 1:
                laps = zip(self.laps[:-1], self.laps[1:])
                return min(map(lambda t: t[1].time - t[0].time, laps))
            else:
                return 0

    def __init__(self, cu, window):
        self.cu = cu
        self.window = window
        self.reset()

        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.lightattr = curses.color_pair(1)

    def reset(self):
        # discard remaining laps
        status = self.cu.status()
        while not isinstance(status, ControlUnit.Status):
            status = self.cu.status()
        self.status = status
        # reset cu timer
        self.cu.reset()
        # reset position tower
        self.cu.clearpos()
        # reset driver info
        self.drivers = list(map(self.Driver, range(1, 9)))
        self.laps = 0
        self.start = None

    def run(self):
        self.window.nodelay(1)
        last = None
        while True:
            try:
                self.update()
                c = self.window.getch()
                if c == ord('q'):
                    break
                elif c == ord('r'):
                    self.reset()
                elif c == ord(' '):
                    self.cu.start()
                data = self.cu.status()
                if data == last:
                    continue
                elif isinstance(data, ControlUnit.Lap):
                    self.handle_lap(data)
                elif isinstance(data, ControlUnit.Status):
                    self.handle_status(data)
                else:
                    pass
                last = data
            except select.error as e:
                pass
            except IOError as e:
                if e.errno != errno.EINTR:
                    raise

    def handle_lap(self, lap):
        if self.start is None:
            self.start = lap.time
        driver = self.drivers[lap.car - 1]
        if self.laps < len(driver.laps):
            self.laps = len(driver.laps)
            self.cu.setlap(self.laps)
        driver.laps.append(lap)

    def handle_status(self, status):
        for driver, fuel in zip(self.drivers, status.fuel):
            driver.fuel = fuel
        for driver, pit in zip(self.drivers, status.pit):
            if driver.pit < pit:
                driver.pits += 1
            driver.pit = pit
        self.status = status

    def update(self):
        window = self.window
        nlines, ncols = window.getmaxyx()
        window.erase()
        window.addstr(0, 0, self.HEADER.ljust(ncols), curses.A_STANDOUT)
        window.addstr(nlines - 1, 0, self.FOOTER)
        window.move(nlines - 1, 0)

        start = self.status.start
        if start == 0 or start == 7:
            pass
        elif start == 1:
            window.chgat(2 * 5, self.lightattr)
        elif start < 7:
            window.chgat(2 * (start - 1), self.lightattr)
        elif int(time.time() * 2) % 2 == 0:  # "manual" blinking
            window.chgat(2 * 5, self.lightattr)

        drivers = [driver for driver in self.drivers if driver.laps]
        for pos, driver in enumerate(sorted(drivers, key=posgetter), start=1):
            if pos == 1:
                leader = driver
                t = formattime(driver.laps[-1].time - self.start, True)
            elif len(driver.laps) == len(leader.laps):
                gap = driver.laps[-1].time - leader.laps[-1].time
                t = '+%ss' % formattime(gap)
            else:
                gap = len(leader.laps) - len(driver.laps)
                t = '+%d Lap%s' % (gap, 's' if gap != 1 else '')
            window.addstr(pos, 0, self.FORMAT.format(
                pos=pos, car=driver.num, time=t, laps=len(driver.laps)-1,
                laptime=formattime(driver.laptime()),
                bestlap=formattime(driver.bestlap()),
                fuel=driver.fuel/15.0, pits=driver.pits
            ))
        window.refresh()

parser = argparse.ArgumentParser(prog='python -m carreralib')
parser.add_argument('device', metavar='DEVICE')
parser.add_argument('-t', '--timeout', default=1.0)
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARN)

with contextlib.closing(ControlUnit(args.device, timeout=args.timeout)) as cu:
    def run(win, args):
        curses.curs_set(0)
        rms = CursesRMS(cu, win)
        rms.run()
    try:
        import curses
        curses.wrapper(run, args)
    except KeyboardInterrupt:
        pass
