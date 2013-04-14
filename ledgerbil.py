#!/usr/bin/python

'''main ledgerbil program file'''

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
import re
from dateutil.parser import parse

from thing import Thing

class Ledgerbil():

    _things = []

    def parseFile(self, afile):
        currentThing = []
        for line in afile:
            if self._isTransactionStart(line):
                self._things.append(Thing(currentThing))
                currentThing = []

            currentThing.append(line)

        if (currentThing):
            self._things.append(Thing(currentThing))

        return True

    def _isTransactionStart(self, line):
        try:
            match = re.match(r'^([-0-9/]{6,})[\s]+[^\s].*$', line)
            if match:
                parse(match.group(1))
                return True
        except:
            pass

        return False

    def printFile(self):
        for thing in self._things:
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
