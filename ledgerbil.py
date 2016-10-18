#!/usr/bin/python

"""main ledgerbil program file"""

from __future__ import print_function

import sys

from arghandler import ArgHandler
from ledgerfile import LedgerFile
from schedulefile import ScheduleFile
from scheduler import Scheduler


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Ledgerbil(object):

    def __init__(self, args):
        self.args = args

    def process_file(self):
        ledgerfile = LedgerFile(self.args.file)

        if self.args.schedule_file:
            schedule_file = ScheduleFile(self.args.schedule_file)
            scheduler = Scheduler(ledgerfile, schedule_file)
            scheduler.run()
            schedule_file.write_file()

        if self.args.sort:
            ledgerfile.sort()

        ledgerfile.write_file()


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]  # pragma: no cover

    args = ArgHandler.get_args(argv)
    ledgerbil = Ledgerbil(args)
    ledgerbil.process_file()

    return 0


if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
