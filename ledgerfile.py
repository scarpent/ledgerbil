#!/usr/bin/python

"""ledger file base class"""

from __future__ import print_function

import sys

from datetime import date
from operator import attrgetter

from ledgerthing import LedgerThing


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LedgerFile(object):

    STARTING_DATE = date(1899, 1, 1)

    def __init__(self, filename):
        self.thingCounter = 0
        self.things = []
        self.filename = filename

        self._parse_file()

    def _open_file(self):
        try:
            self.ledger_file = open(self.filename, 'r+')
        except IOError as e:
            sys.stderr.write('error: %s\n' % e)
            sys.exit(-1)

    def _close_file(self):
        self.ledger_file.close()

    def _parse_file(self):
        self._open_file()
        self._parse_lines(self.ledger_file.read().splitlines())
        self._close_file()

    def _parse_lines(self, lines):
        current_lines = []
        for line in lines:
            if LedgerThing.is_new_thing(line):
                self._add_thing_lines(current_lines)
                current_lines = []

            current_lines.append(line)

        self._add_thing_lines(current_lines)

    def _add_thing_lines(self, lines):
        if lines:
            thing = LedgerThing(lines)
            self.add_thing(thing)

    def add_thing(self, thing):
        things = [thing]
        self.add_things(things)

    def add_things(self, things):
        for thing in things:
            thing.thingNumber = self.thingCounter
            self.get_things().append(thing)
            # increment after for a zero-based array
            self.thingCounter += 1

    def get_things(self):
        return self.things

    def sort(self):
        current_date = self.STARTING_DATE

        for thing in self.get_things():
            if thing.thingDate is None:
                thing.thingDate = current_date
            else:
                current_date = thing.thingDate

        self.get_things().sort(
            key=attrgetter('thingDate', 'thingNumber')
        )

    def print_file(self):
        for thing in self.get_things():
            for line in thing.get_lines():
                print(line)

    def write_file(self):
        self._open_file()
        for thing in self.get_things():
            for line in thing.get_lines():
                self.ledger_file.write(line + '\n')
        self._close_file()
