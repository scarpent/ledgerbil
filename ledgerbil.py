#!/usr/bin/python

from __future__ import print_function

import sys
import os

class Ledgerbil():

    filelines = []

    def parsefile(self, filename):
        try:
            file = open(filename)
        except IOError:
            return False

        for line in file:
            self.filelines.append(line)
            
        return True

    def printfile(self):
        for line in self.filelines:
            print(line, end='')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print('please specify a file')
        sys.exit(1)

    ledgerbil = Ledgerbil()

    ledgerbil.parsefile(argv[0])
    ledgerbil.printfile()

if __name__ == "__main__":
    sys.exit(main())
