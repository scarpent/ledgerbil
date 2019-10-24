import argparse
from textwrap import dedent

from .ledgerbilexceptions import LdgReconcilerError
from .ledgerfile import LedgerFile
from .reconciler import reconciled_status, run_reconciler
from .scheduler import print_next_scheduled_date, run_scheduler
from .util import handle_error


def run_ledgerbil(args):

    if args.next_scheduled_date:
        if not args.schedule:
            return handle_error("error: -s/--schedule is required")
        return print_next_scheduled_date(args.schedule)

    if args.reconciled_status:
        return reconciled_status()

    if not args.file:
        return handle_error("error: -f/--file is required")

    try:
        ledgerfiles = [LedgerFile(f, args.reconcile) for f in args.file]
    except LdgReconcilerError as e:
        return handle_error(str(e))

    if args.reconcile:
        if not matching_account_found(ledgerfiles, args.reconcile):
            return
        return run_reconciler(ledgerfiles)

    if args.schedule:
        error = run_scheduler(ledgerfiles[0], args.schedule)
        if error:
            return error

    if args.sort:
        for ledgerfile in ledgerfiles:
            ledgerfile.sort()
            ledgerfile.write_file()


def matching_account_found(ledgerfiles, reconcile_account):
    if any(lf.rec_account_matched for lf in ledgerfiles):
        return True
    else:
        print(f'No matching account found for "{reconcile_account}"')
        return False


def get_args(args):
    program = "ledgerbil/main.py"
    description = dedent(
        """\
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
    """
    )
    scripts_description = dedent(
        f"""\
        other commands (run with -h to see command help):
            {program}
                grid                    ledger reports in year/month tables
                investments (or inv)    nicer view of shares and dollars
                pass                    passthrough to ledger
                portfolio (or port)     standalone investment tracker
        """
    )

    parser = argparse.ArgumentParser(
        prog=program,
        description=description,
        epilog=scripts_description,
        formatter_class=(
            lambda prog: argparse.RawDescriptionHelpFormatter(
                prog, max_help_position=40, width=71
            )
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        action="append",
        default=[],
        help="ledger file(s) to be processed",
    )
    parser.add_argument(
        "-S", "--sort", action="store_true", help="sort the file(s) by transaction date"
    )
    parser.add_argument(
        "-r",
        "--reconcile",
        type=str,
        metavar="ACCT",
        help=(
            "interactively reconcile ledger file(s) with this account regex; "
            "scheduler/sort have no effect if also specified"
        ),
    )
    parser.add_argument(
        "-R",
        "--reconciled-status",
        action="store_true",
        help=(
            "show accounts where reconciler previous balance "
            "differs from cleared balance in ledger"
        ),
    )
    parser.add_argument(
        "-s",
        "--schedule",
        type=str,
        metavar="FILE",
        help=(
            "scheduled transactions file, with new entries to be added to -f ledger "
            "file; if given multiple ledger files, will use the first; if --sort also "
            "specified, sorts the ledger file after entries have been added"
        ),
    )
    parser.add_argument(
        "-n",
        "--next-scheduled-date",
        action="store_true",
        help="show the date of the next scheduled transaction",
    )

    if not args:
        parser.print_help()

    return parser.parse_args(args)


def main(argv=None):
    args = get_args(argv or [])
    return run_ledgerbil(args)
