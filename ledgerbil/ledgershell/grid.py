import argparse
import re
from pprint import pprint

from .runner import get_ledger_output

LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')


def get_stuff(args):
    column_dictionary = get_column(args.ledger)
    pprint(column_dictionary)


def get_column(ledger_options):
    ACCOUNT = 1
    DOLLARS = 0

    lines = get_ledger_output(ledger_options).split('\n')
    column = {}
    for line in lines:
        if line == '' or line[0] == '-':
            break
        match = re.match(LINE_REGEX, line)
        assert match, f'Line regex did not match: {line}'
        column[match.groups()[ACCOUNT]] = match.groups()[DOLLARS]

    return column


def get_args(args=[]):
    parser = argparse.ArgumentParser(
        prog='ledgerbil/main.py grid',
        formatter_class=(lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=40,
            width=100
        ))
    )
    parser.add_argument(
        '-a', '--accounts',
        type=str,
        help='grid for specified accounts'
    )
    parser.add_argument(
        '-l', '--ledger',
        type=str,
        help='ledgerbil passthrough (perhaps temporary)'
    )

    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    get_stuff(args)
