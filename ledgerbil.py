#!/usr/bin/python

"""main ledgerbil program file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
import argparse

from thing import LedgerThing
from operator import attrgetter


class Ledgerbil():

    sort = False

    def __init__(self):
        self.things = []

    def parseFile(self, afile):
        return self.parseLines(afile.read().splitlines())

    def parseLines(self, lines):
        currentLines = []
        i = 0
        for line in lines:
            i += 1
            #sys.stderr.write('%d) %s' % (i, line))
            # if first line a new "thing," currentLines will be empty
            if LedgerThing.isNewThing(line) and currentLines:
                self.things.append(LedgerThing(currentLines))
                currentLines = []

            currentLines.append(line)

        #currentLines.append('\n')
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
            # sys.stderr.write('-->%s %s <--\n' %
            #                  (thing.thingNumber, thing.date))
            for line in thing.getLines():
                i += 1
                #sys.stderr.write('%d) %s' % (i, line))
                print(line)

    def sortThings(self):
        self.things.sort(key=attrgetter('date', 'thingNumber'))


def main():

    ledgerbil = Ledgerbil()

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='ledger file to be processed')
    args = parser.parse_args()

    try:
        filename = args.file
        afile = open(filename, 'r')
    except IOError as e:
        print('error: %s' % e)
        return -1

    ledgerbil.parseFile(afile)

    #ledgerbil.sortThings()
    ledgerbil.printFile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
