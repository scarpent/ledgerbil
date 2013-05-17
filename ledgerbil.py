#!/usr/bin/python

"""main ledgerbil program file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys

from ledgerfile import LedgerFile
from arghandler import ArgHandler


class Ledgerbil():

    def __init__(self, args):
        self.args = args

    def processFile(self):
        ledgerFile = LedgerFile(self.args.file)

        if self.args.sort:
            ledgerFile.sort()

        ledgerFile.printFile()

def main():
    args = ArgHandler.getArgs()
    ledgerbil = Ledgerbil(args)
    ledgerbil.processFile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
