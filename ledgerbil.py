#!/usr/bin/python

from __future__ import print_function

import sys
import os

class Ledgerbil():

    def parseFile(self, filename):
        try:
            file = open(filename)
        except IOError:
            return False

        for line in file:
            print(line, end='')
        return True

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print('please specify a file')
        sys.exit(1)

    ledgerbil = Ledgerbil()

    ledgerbil.parseFile(argv[0])

if __name__ == "__main__":
    sys.exit(main())
