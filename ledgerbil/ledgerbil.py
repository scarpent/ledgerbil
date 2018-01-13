import sys

from .arghandler import get_args
from .ledgerbilexceptions import LdgReconcilerError, LdgSchedulerError
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
                return self.error('error: -S/--schedule-file is required')
            try:
                schedule_file = ScheduleFile(self.args.schedule_file)
            except LdgSchedulerError as e:
                return self.error(str(e))
            print(schedule_file.next_scheduled_date())
            return 0

        if not self.args.file:
            return self.error('error: -f/--file is required')

        try:
            ledgerfile = LedgerFile(self.args.file, self.args.reconcile)
        except LdgReconcilerError as e:
            return self.error(str(e))

        if self.args.schedule_file:
            try:
                schedule_file = ScheduleFile(self.args.schedule_file)
            except LdgSchedulerError as e:
                return self.error(str(e))
            scheduler = Scheduler(ledgerfile, schedule_file)
            scheduler.run()
            schedule_file.write_file()
            ledgerfile.write_file()

        if self.args.sort:
            ledgerfile.sort()
            ledgerfile.write_file()

        if self.args.reconcile:
            if ledgerfile.rec_account_matched:
                try:
                    reconciler = Reconciler(ledgerfile)
                except LdgReconcilerError as e:
                    return self.error(str(e))

                reconciler.cmdloop()
            else:
                print(f'No matching account found for "{self.args.reconcile}"')

        return 0

    def error(self, message):
        print(message, file=sys.stderr)
        return -1


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    args = get_args(argv)
    ledgerbil = Ledgerbil(args)

    return ledgerbil.process_file()
