import argparse
import re
from collections import defaultdict
from textwrap import dedent

from .. import util
from ..colorable import Colorable
from .runner import get_ledger_output

LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')


def get_grid_report(args, ledger_args=[]):
    unit = 'month' if args.month else 'year'
    period_names = sorted(get_period_names(args, ledger_args, unit))
    accounts, columns = get_columns(period_names, ledger_args, args.depth)
    grid = get_grid(accounts, columns)
    return get_flat_report(grid, accounts, columns, period_names)


def get_flat_report(grid, accounts, columns, period_names):
    COL_PERIOD = 14

    headers = [f'{pn:>{COL_PERIOD}}' for pn in period_names + ['total']]
    report = f"{Colorable('white', ''.join(headers))}\n"
    for account in sorted(accounts):
        account_f = Colorable('blue', account)
        amounts = [grid[account].get(pn, 0) for pn in period_names]
        amounts_f = [util.get_colored_amount(
            amount,
            colwidth=COL_PERIOD,
            positive='yellow',
            zero='grey'
        ) for amount in amounts]
        row_total = util.get_colored_amount(sum(amounts), colwidth=COL_PERIOD)
        report += f"{''.join(amounts_f)}{row_total}  {account_f}\n"

    dashes = [
        f"{'-' * (COL_PERIOD - 2):>{COL_PERIOD}}" for x in period_names + [1]
    ]
    report += f"{Colorable('white', ''.join(dashes))}\n"

    totals = [sum(columns[pn].values()) for pn in period_names]
    totals_f = [util.get_colored_amount(t, COL_PERIOD) for t in totals]
    row_total = util.get_colored_amount(sum(totals), colwidth=COL_PERIOD)

    report += f"{''.join(totals_f)}{row_total}\n"
    return report


def get_period_names(args, ledger_args, unit='year'):
    # --collapse behavior seems suspicous, but --empty
    # appears to work for our purposes here
    # groups.google.com/forum/?fromgroups=#!topic/ledger-cli/HAKAMYiaL7w
    begin = ['-b', args.begin] if args.begin else []
    end = ['-e', args.end] if args.end else []
    period = ['-p', args.period] if args.period else []

    if unit == 'year':
        period_options = ['--yearly', '-y', '%Y']
        period_len = 4
    else:
        period_options = ['--monthly', '-y', '%Y/%m']
        period_len = 7

    lines = get_ledger_output([
        'reg'
    ] + begin + end + period + period_options + [
        '--collapse',
        '--empty'
    ] + ledger_args).split('\n')

    return {x[:period_len] for x in lines if x[:period_len].strip() != ''}


def get_columns(period_names, ledger_args, depth=0):
    accounts = set()
    columns = {}
    for period_name in period_names:
        column = get_column(
            ['bal', '--flat', '-p', period_name] + ledger_args,
            depth
        )
        accounts.update(column.keys())
        columns[period_name] = column

    return accounts, columns


def get_column(ledger_args, depth=0):
    ACCOUNT = 1
    DOLLARS = 0

    lines = get_ledger_output(ledger_args).split('\n')
    column = defaultdict(int)
    for line in lines:
        if line == '' or line[0] == '-':
            break
        match = re.match(LINE_REGEX, line)
        # should match as long as --market is used?
        assert match, f'Line regex did not match: {line}'
        amount = float(match.groups()[DOLLARS].replace(',', ''))
        account = match.groups()[ACCOUNT]
        if depth > 0:
            account_parts = account.split(':')
            account = ':'.join(account_parts[:depth])
        column[account] += amount

    return column


def get_grid(accounts, columns):
    grid = {key: {} for key in accounts}
    for period_name, column in columns.items():
        for account, amount in column.items():
            grid[account][period_name] = amount

    return grid


def get_args(args=[]):
    program = 'ledgerbil/main.py grid'
    description = dedent('''\
        Show ledger balance report in tabular form with years or months as the
        columns. Begin, end, and period params are handled as ledger interprets
        them, and all arguments not defined here are passed through to ledger.

        Don't specify bal, balance, reg, or register!

        e.g. ./main.py expenses -p 'last 2 years'

        Will show expenses for last two years with separate columns for the
        years.

        Currently supports ledger --flat reports. (Although you don't have to
        specify --flat.)
    ''')
    parser = argparse.ArgumentParser(
        prog=program,
        description=description,
        formatter_class=(lambda prog: argparse.RawTextHelpFormatter(
            prog,
            max_help_position=40,
            width=100
        ))
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-y', '--year',
        action='store_true',
        default=True,
        help='year grid (default)'
    )
    group.add_argument(
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
        help='end date'
    )
    parser.add_argument(
        '-p', '--period',
        type=str,
        help='period expression'
    )
    parser.add_argument(
        '--depth',
        type=int,
        metavar='N',
        default=0,
        help='limit the depth of account tree'
    )

    # workaround for problems with nargs=argparse.REMAINDER
    # see: https://bugs.python.org/issue17050
    return parser.parse_known_args(args)


def main(argv=[]):
    args, ledger_args = get_args(argv)
    print(get_grid_report(args, ledger_args))
