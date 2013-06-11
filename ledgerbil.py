#!/usr/bin/python

"""main ledgerbil program file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys

from arghandler import ArgHandler
from ledgerfile import LedgerFile
from schedulefile import ScheduleFile
from scheduler import Scheduler


class Ledgerbil(object):

    def __init__(self, args):
        self.args = args

    def processFile(self):
        ledgerfile = LedgerFile(self.args.file)

        if self.args.schedule_file:
            schedulefile = ScheduleFile(self.args.schedule_file)
            schedulefile.sort()
            scheduler = Scheduler(ledgerfile, schedulefile)
            scheduler.run()


        if self.args.sort:
            ledgerfile.sort()

        ledgerfile.writeFile()

def main():
    args = ArgHandler.getArgs()
    ledgerbil = Ledgerbil(args)
    ledgerbil.processFile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
