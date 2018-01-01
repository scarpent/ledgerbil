import argparse


def get_args(args):
    parser = argparse.ArgumentParser(
        prog='ledgerbil.py',
        formatter_class=(
            lambda prog: argparse.HelpFormatter(
                prog,
                max_help_position=36
            )
        )
    )

    parser.add_argument(
        '-f', '--file',
        type=str,
        help='ledger file to be processed'
    )
    parser.add_argument(
        '-s', '--sort',
        action='store_true',
        help='sort the file by transaction date'
    )
    parser.add_argument(
        '-r', '--reconcile',
        type=str, metavar='ACCT',
        help='interactively reconcile the specified account'
    )
    parser.add_argument(
        '-S', '--schedule-file',
        type=str, metavar='FILE',
        help=(
            'file with scheduled transactions '
            '(to be added to -f ledger file)'
        )
    )
    parser.add_argument(
        '-n', '--next-scheduled-date',
        action='store_true',
        help='show the date of the next scheduled transaction'
    )

    return parser.parse_args(args)
