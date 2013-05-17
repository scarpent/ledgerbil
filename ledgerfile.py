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

    def __init__(self, filename):
        self.thingCounter = 0
        self.currentDate = '1899/01/01'
        self.things = []

        self.ledgerFile = self.openFile(filename)
        self.parseFile()

    def openFile(self, filename):
        try:
            self.ledgerFile = open(filename, 'r+')
        except IOError as e:
            sys.stderr.write('error: %s\n' % e)
            sys.exit(-1)

    def parseFile(self):
        self.parseLines(self.ledgerFile.read().splitlines())

    def parseLines(self, lines):
        currentLines = []
        for line in lines:
            if LedgerThing.isNewThing(line):
                self.addThing(currentLines)
                currentLines = []

            currentLines.append(line)

        self.addThing(currentLines)

    def addThing(self, currentLines):
        if currentLines:
            self.thingCounter += 1
            thing = LedgerThing(
                currentLines,
                self.thingCounter,
                self.currentDate
            )
            self.currentDate = thing.date
            self.things.append(thing)

    def getThings(self):
        return self.things

    def sortFile(self):
        self.things.sort(key=attrgetter('date', 'thingNumber'))

    def printFile(self):
        for thing in self.things:
            for line in thing.getLines():
                print(line)

    def writeFile(self):
        self.ledgerFile.seek(0)
        for thing in self.things:
                self.ledgerFile.writelines(thing.getLines())
