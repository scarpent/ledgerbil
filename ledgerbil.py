#!/usr/bin/python

'''main ledgerbil program file'''

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys

from thing import LedgerThing


class Ledgerbil():

    things = []

    def __init__(self):
        self.things = []

    def parseFile(self, afile):
        currentLines = []
        for line in afile:
            if LedgerThing.isNewThing(line):
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
        for thing in self.things:
            for line in thing.getLines():
                print(line, end='')


def main(argv=None):

    ledgerbil = Ledgerbil()

    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        ledgerbil.parseFile(sys.stdin)
    else:
        try:
            filename = argv[1]
            afile = open(filename, 'r')
        except IOError as e:
            print('error: %s' % e)
            return -1

        ledgerbil.parseFile(afile)

    ledgerbil.printFile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
