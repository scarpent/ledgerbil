#!/usr/bin/python

"""ledger files: journal, schedule file, or preview file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
from operator import attrgetter

from thing import LedgerThing


class LedgerFile():

    startingDate = '1899/01/01'

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
                self.addThing(currentLines)
                currentLines = []

            currentLines.append(line)

        self.addThing(currentLines)

    def addThing(self, lines):
        if lines:
            self.thingCounter += 1
            thing = LedgerThing(lines, self.thingCounter)
            self.things.append(thing)

    def getThings(self):
        return self.things

    def sort(self):
        currentDate = self.startingDate

        for thing in self.things:
            if thing.date is None:
                thing.date = currentDate
            else:
                currentDate = thing.date

        self.things.sort(key=attrgetter('date', 'thingNumber'))

    def printFile(self):
        for thing in self.things:
            for line in thing.getLines():
                print(line)

    def writeFile(self):
        self._openFile()
        for thing in self.things:
            for line in thing.getLines():
                self.ledgerFile.write(line + '\n')
        self._closeFile()
