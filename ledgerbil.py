#!/usr/bin/python

"""main ledgerbil program file"""

from __future__ import print_function

import sys

from arghandler import ArgHandler
from ledgerfile import LedgerFile
from schedulefile import ScheduleFile
from scheduler import Scheduler


__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Ledgerbil(object):

    def __init__(self, args):
        self.args = args

    def processFile(self):
        ledgerfile = LedgerFile(self.args.file)

        if self.args.schedule_file:
            schedulefile = ScheduleFile(self.args.schedule_file)
            scheduler = Scheduler(ledgerfile, schedulefile)
            scheduler.run()

        if self.args.sort:
            ledgerfile.sort()

        ledgerfile.writeFile()
        if self.args.schedule_file:
            schedulefile.writeFile()

def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]  # pragma: no cover

    args = ArgHandler.getArgs(argv)
    ledgerbil = Ledgerbil(args)
    ledgerbil.processFile()

    return 0

if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
