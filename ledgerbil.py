#!/usr/bin/env python

"""main ledgerbil program file"""

from __future__ import print_function

import sys

from arghandler import ArgHandler
from ledgerbilexceptions import LdgReconcilerMoreThanOneMatchingAccount
from ledgerbilexceptions import LdgReconcilerMultipleStatuses
from ledgerfile import LedgerFile
from reconciler import Reconciler
from schedulefile import ScheduleFile
from scheduler import Scheduler


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Ledgerbil(object):

    def __init__(self, args):
        self.args = args

    def process_file(self):
        try:
            ledgerfile = LedgerFile(self.args.file, self.args.reconcile)
        except LdgReconcilerMoreThanOneMatchingAccount as e:
            print('Reconcile error. More than one matching account:')
            for account in e.message:
                print('    ' + account)
            return 2
        except LdgReconcilerMultipleStatuses as e:
            print(str(e))
            return 4

        if self.args.schedule_file:
            schedule_file = ScheduleFile(self.args.schedule_file)
            scheduler = Scheduler(ledgerfile, schedule_file)
            scheduler.run()
            schedule_file.write_file()

        if self.args.sort:
            ledgerfile.sort()

        if self.args.reconcile:
            if ledgerfile.rec_account_matches:
                reconciler = Reconciler(ledgerfile, self.args.reconcile)
                reconciler.cmdloop()
            else:
                print('No matching account found for "{acct}"'.format(
                    acct=self.args.reconcile
                ))

        ledgerfile.write_file()

        return 0


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]  # pragma: no cover

    args = ArgHandler.get_args(argv)
    ledgerbil = Ledgerbil(args)
    return ledgerbil.process_file()


if __name__ == "__main__":
    sys.exit(main())        # pragma: no cover
