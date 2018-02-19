import argparse
import re
from pprint import pprint

from .runner import get_ledger_output

LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')


def get_grid_report(args, ledger_args=[]):
    # todo: pending other options, goal is to have year be the
    #       default without explicitly settings as the default
    if args.month:
        return('only year grid is wip...')
    else:
        years = get_included_years(args, ledger_args)

    all_accounts = set()
    all_years = {}
    for year in years:
        column = get_column(f'bal expenses --flat -p {year}')
        all_accounts.update(column.keys())
        all_years[year] = column

    pprint(all_years)
    return all_accounts


def get_included_years(args, ledger_args):
    # todo: would like to add --collapse but not working with sample data...
    # https://groups.google.com/forum/?fromgroups=#!topic/ledger-cli/HAKAMYiaL7w  # noqa
    begin = f'-b {args.begin} ' if args.begin else ''
    end = f'-e {args.end} ' if args.end else ''
    period = f'-p {args.period} ' if args.period else ''

    options = ' '.join(ledger_args)

    lines = get_ledger_output(
        f'reg {begin}{end}{period}--yearly --total-data {options}'
    ).split('\n')

    return {x[:4] for x in lines if x}


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
        '-y', '--year',
        action='store_true',
        default=True,
        help='year grid'
    )
    parser.add_argument(
        '-m', '--month',
        action='store_true',
        help='month grid'
    )
    parser.add_argument(
        '-b', '--begin',
        type=str,
        metavar='DATE',
        help='begin date'
    )
    parser.add_argument(
        '-e', '--end',
        type=str,
        metavar='DATE',
        help='begin date'
    )
    parser.add_argument(
        '-p', '--period',
        type=str,
        help='period expression'
    )
    parser.add_argument(
        '-l', '--ledger',
        action='store_true',
        help='ledgerbil passthrough'
    )

    # workaround for problems with nargs=argparse.REMAINDER
    # see: https://bugs.python.org/issue17050
    return parser.parse_known_args(args)


def main(argv=[]):
    args, ledger_args = get_args(argv)
    if args.ledger:
        print(get_ledger_output(' '.join(ledger_args)))
        return

    pprint(get_grid_report(args, ledger_args))
