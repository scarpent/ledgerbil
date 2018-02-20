import argparse
import re

from .. import util
from .runner import get_ledger_output

LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')


def get_grid_report(args, ledger_args=[]):
    unit = 'month' if args.month else 'year'
    period_names = sorted(get_period_names(args, ledger_args, unit))
    accounts, columns = get_columns(period_names, ledger_args)
    grid = get_grid(accounts, columns)
    return get_formatted_report(grid, accounts, columns, period_names)


def get_formatted_report(grid, accounts, columns, period_names):
    COL_ACCOUNT = 48
    COL_PERIOD = 14

    headers = [f'{pn:>{COL_PERIOD}}' for pn in period_names]
    report = f"{' ' * COL_ACCOUNT}{''.join(headers)}{'total':>{COL_PERIOD}}\n"
    for account in sorted(accounts):
        amounts = [grid[account].get(pn, 0) for pn in period_names]
        amounts_f = [util.get_colored_amount(
            amount,
            colwidth=COL_PERIOD,
            positive='yellow',
            zero='grey'
        ) for amount in amounts]
        row_total = util.get_colored_amount(sum(amounts), colwidth=COL_PERIOD)
        report += f"{account:{COL_ACCOUNT}}{''.join(amounts_f)}{row_total}\n"

    dashes = [
        f"{'-' * (COL_PERIOD - 2):>{COL_PERIOD}}" for x in period_names + [1]
    ]
    report += f"{' ' * COL_ACCOUNT}{''.join(dashes)}\n"

    totals = [sum(columns[pn].values()) for pn in period_names]
    totals_f = [util.get_colored_amount(t, COL_PERIOD) for t in totals]
    row_total = util.get_colored_amount(sum(totals), colwidth=COL_PERIOD)

    report += f"{' ' * COL_ACCOUNT}{''.join(totals_f)}{row_total}\n"
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


def get_columns(period_names, ledger_args):
    accounts = set()
    columns = {}
    for period_name in period_names:
        column = get_column(['bal', '--flat', '-p', period_name] + ledger_args)
        accounts.update(column.keys())
        columns[period_name] = column

    return accounts, columns


def get_column(ledger_args):
    ACCOUNT = 1
    DOLLARS = 0

    lines = get_ledger_output(ledger_args).split('\n')
    column = {}
    for line in lines:
        if line == '' or line[0] == '-':
            break
        match = re.match(LINE_REGEX, line)
        # should match as long as --market is used?
        assert match, f'Line regex did not match: {line}'
        amount = float(match.groups()[DOLLARS].replace(',', ''))
        column[match.groups()[ACCOUNT]] = amount

    return column


def get_grid(accounts, columns):
    grid = {key: {} for key in accounts}
    for period_name, column in columns.items():
        for account, amount in column.items():
            grid[account][period_name] = amount

    return grid


def get_args(args=[]):
    parser = argparse.ArgumentParser(
        prog='ledgerbil/main.py grid',
        formatter_class=(lambda prog: argparse.HelpFormatter(
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
        help='year grid'
    )
    group.add_argument(
        '-m', '--month',
        action='store_true',
        help='month grid'
    )
    # todo: --depth option (can't use ledger's --depth with --flat)
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

    # workaround for problems with nargs=argparse.REMAINDER
    # see: https://bugs.python.org/issue17050
    return parser.parse_known_args(args)


def main(argv=[]):
    args, ledger_args = get_args(argv)
    print(get_grid_report(args, ledger_args))
