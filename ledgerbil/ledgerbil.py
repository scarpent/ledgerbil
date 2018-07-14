import argparse
from textwrap import dedent

from .ledgerbilexceptions import LdgReconcilerError
from .ledgerfile import LedgerFile
from .reconciler import get_reconciler_cache, run_reconciler
from .scheduler import print_next_scheduled_date, run_scheduler
from .util import handle_error


class Ledgerbil:

    def __init__(self, args):
        self.args = args
        self.ledgerfiles = None

    def run(self):

        if self.args.next_scheduled_date:
            if not self.args.schedule:
                return handle_error('error: -s/--schedule is required')
            return print_next_scheduled_date(self.args.schedule)

        if self.args.reconcile_status:  # pragma: no cover (coming soon...)
            return self.reconcile_status()

        if not self.args.file:
            return handle_error('error: -f/--file is required')

        try:
            self.ledgerfiles = [
                LedgerFile(f, self.args.reconcile) for f in self.args.file
            ]
        except LdgReconcilerError as e:
            return handle_error(str(e))

        if self.args.reconcile:
            if self.no_matching_account_found():
                return
            return run_reconciler(self.ledgerfiles)

        if self.args.schedule:
            error = run_scheduler(self.ledgerfiles[0], self.args.schedule)
            if error:
                return error

        if self.args.sort:
            for ledgerfile in self.ledgerfiles:
                ledgerfile.sort()
                ledgerfile.write_file()

    def no_matching_account_found(self):
        if not any(lf.rec_account_matched for lf in self.ledgerfiles):
            print(f'No matching account found for "{self.args.reconcile}"')
            return True
        else:
            return False

    def reconcile_status(self):  # pragma: no cover
        from pprint import pprint
        pprint(get_reconciler_cache())


def get_args(args):
    program = 'ledgerbil/main.py'
    description = dedent('''\
        ledgerbil works with ledger cli files. It supports a vague subset of
        ledger as used and tested by its author.

        It is biased, if not welded, to dollars as the default commodity, but
        the author would happily aspire to more flexibility with the help of
        motivated contributors or users. (Similarly it assumes commas as the
        thousands separator but certainly this shouldn't be insurmountable to
        modify for an international community.)

        Some features work on ledger files independently of the ledger cli
        program itself, while others use ledger to report on ledger data in
        ways not currently supported by ledger. (Or at least, in ways not
        understood by the author.)

        See settings.py.example for config options with the "other commands"
        below. (These are "ledgershell" scripts which use the ledger client.)
    ''')
    scripts_description = dedent(f'''\
        other commands (run with -h to see command help):
            {program}
                grid                    ledger reports in year/month tables
                investments (or inv)    nicer view of shares and dollars
                pass                    passthrough to ledger
                portfolio (or port)     standalone investment tracker
                prices                  download mutual fund prices
        ''')

    parser = argparse.ArgumentParser(
        prog=program,
        description=description,
        epilog=scripts_description,
        formatter_class=(lambda prog: argparse.RawDescriptionHelpFormatter(
            prog,
            max_help_position=40,
            width=71
        ))
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        action='append',
        default=[],
        help='ledger file(s) to be processed'
    )
    parser.add_argument(
        '-S', '--sort',
        action='store_true',
        help='sort the file(s) by transaction date'
    )
    parser.add_argument(
        '-r', '--reconcile',
        type=str,
        metavar='ACCT',
        help='interactively reconcile ledger file(s) with this account regex; '
             'scheduler/sort have no effect if also specified'
    )
    parser.add_argument(
        '-R', '--reconcile-status',
        action='store_true',
        help='show last reconcilation status for accounts'
    )
    parser.add_argument(
        '-s', '--schedule',
        type=str,
        metavar='FILE',
        help='scheduled transactions file, with new entries to be added to '
             '-f ledger file; if given multiple ledger files, will use the '
             'first; if --sort also specified, sorts the ledger file after '
             'entries have been added'
    )
    parser.add_argument(
        '-n', '--next-scheduled-date',
        action='store_true',
        help='show the date of the next scheduled transaction'
    )

    if not args:
        parser.print_help()

    return parser.parse_args(args)


def main(argv=None):
    args = get_args(argv or [])
    ledgerbil = Ledgerbil(args)

    return ledgerbil.run()
