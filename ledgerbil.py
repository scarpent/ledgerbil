#!/usr/bin/python

'''main ledgerbil program file'''

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
import os

class Ledgerbil():

    filelines = []

    def parsefile(self, file):

        self.filelines = file.readlines()

        return True

    def printfile(self):
        for line in self.filelines:
            print(line, end='')


def main(argv=None):

    ledgerbil = Ledgerbil()

    if argv is None:
        argv = sys.argv
    if len(argv) < 2:
        ledgerbil.parsefile(sys.stdin)
    else:
        try:
            filename = argv[1]
            file = open(filename, 'r')
        except IOError as e:
            print('error: %s' % e)
            return -1

        ledgerbil.parsefile(file)

    ledgerbil.printfile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
