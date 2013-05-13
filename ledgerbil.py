#!/usr/bin/python

"""main ledgerbil program file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
from operator import attrgetter

from thing import LedgerThing
from arghandler import ArgHandler

class Ledgerbil():

    def __init__(self, args):
        self.things = []
        self.args = args

    def parseFile(self, afile):
        self.parseLines(afile.read().splitlines())
        if self.args.sort:
            self.sortThings()

        return True

    def parseLines(self, lines):
        currentLines = []
        i = 0
        for line in lines:
            i += 1
            # if first line a new "thing," currentLines will be empty
            if LedgerThing.isNewThing(line) and currentLines:
                self.things.append(LedgerThing(currentLines))
                currentLines = []

            currentLines.append(line)

        if currentLines:
            self.things.append(LedgerThing(currentLines))

        return True

    def getFileLines(self):
        fileLines = []
        for thing in self.things:
            fileLines.extend(thing.getLines())

        return fileLines

    def printFile(self):
        i = 0
        for thing in self.things:
            for line in thing.getLines():
                i += 1
                print(line)

    def sortThings(self):
        self.things.sort(key=attrgetter('date', 'thingNumber'))


def main():

    args = ArgHandler.getArgs()

    # todo: move file handling into class
    try:
        afile = open(args.file, 'r')
    except IOError as e:
        print('error: %s' % e)
        return -1

    ledgerbil = Ledgerbil(args)

    ledgerbil.parseFile(afile)
    ledgerbil.printFile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
