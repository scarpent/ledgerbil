#!/usr/bin/python

"""ledger file base class"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
from datetime import date
from operator import attrgetter

from ledgerthing import LedgerThing


class LedgerFile(object):

    STARTING_DATE = date(1899, 1, 1)

    def __init__(self, filename):
        self.thingCounter = 0
        self.things = []
        self.filename = filename

        self._parseFile()

    def _openFile(self):
        try:
            self.ledgerFile = open(self.filename, 'r+')
        except IOError as e:
            sys.stderr.write('error: %s\n' % e)
            sys.exit(-1)

    def _closeFile(self):
        self.ledgerFile.close()

    def _parseFile(self):
        self._openFile()
        self._parseLines(self.ledgerFile.read().splitlines())
        self._closeFile()

    def _parseLines(self, lines):
        currentLines = []
        for line in lines:
            if LedgerThing.isNewThing(line):
                self._addThingLines(currentLines)
                currentLines = []

            currentLines.append(line)

        self._addThingLines(currentLines)

    def _addThingLines(self, lines):
        if lines:
            thing = LedgerThing(lines)
            self.addThing(thing)

    def addThing(self, thing):
        things = [thing]
        self.addThings(things)

    def addThings(self, things):
        for thing in things:
            thing.thingNumber = self.thingCounter
            self.getThings().append(thing)
            # increment after for a zero-based array
            self.thingCounter += 1

    def getThings(self):
        return self.things

    def sort(self):
        currentDate = self.STARTING_DATE

        for thing in self.getThings():
            if thing.thingDate is None:
                thing.thingDate = currentDate
            else:
                currentDate = thing.thingDate

        self.getThings().sort(key=attrgetter('thingDate', 'thingNumber'))

    def printFile(self):
        for thing in self.getThings():
            for line in thing.getLines():
                print(line)

    def write_file(self):
        self._openFile()
        for thing in self.getThings():
            for line in thing.getLines():
                self.ledgerFile.write(line + '\n')
        self._closeFile()
