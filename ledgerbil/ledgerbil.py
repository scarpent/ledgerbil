import sys

from .arghandler import ArgHandler
from .ledgerfile import LedgerFile
from .reconciler import Reconciler
from .schedulefile import ScheduleFile
from .scheduler import Scheduler


class Ledgerbil(object):

    def __init__(self, args):
        self.args = args

    def process_file(self):

        if self.args.next_scheduled_date:
            if not self.args.schedule_file:
                print('error: -S/--schedule-file is required')
                return -1

            schedule_file = ScheduleFile(self.args.schedule_file)
            print(schedule_file.next_scheduled_date())
            return 0

        if not self.args.file:
            print('error: -f/--file is required')
            return -1

        ledgerfile = LedgerFile(self.args.file, self.args.reconcile)

        if self.args.schedule_file:
            schedule_file = ScheduleFile(self.args.schedule_file)
            scheduler = Scheduler(ledgerfile, schedule_file)
            scheduler.run()
            schedule_file.write_file()
            ledgerfile.write_file()

        if self.args.sort:
            ledgerfile.sort()
            ledgerfile.write_file()

        if self.args.reconcile:
            if ledgerfile.rec_account_matches:  # pragma: no cover
                reconciler = Reconciler(ledgerfile)
                reconciler.cmdloop()
            else:
                print('No matching account found for "{acct}"'.format(
                    acct=self.args.reconcile
                ))

        return 0


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]  # pragma: no cover

    args = ArgHandler.get_args(argv)
    ledgerbil = Ledgerbil(args)

    return ledgerbil.process_file()
