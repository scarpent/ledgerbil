import argparse
import re
import shlex
from pprint import pprint  # noqa

from .. import util
from .runner import get_ledger_command, get_ledger_output

LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')


def get_grid_report(args, ledger_args=[]):
    unit = 'month' if args.month else 'year'
    periods = sorted(get_included_periods(args, ledger_args, unit))

    all_accounts = set()
    all_periods = {}
    for period in periods:
        column = get_column(['bal', '--flat', '-p', period] + ledger_args)
        all_accounts.update(column.keys())
        all_periods[period] = column

    grid = {key: {} for key in all_accounts}

    for period, column in all_periods.items():
        for account, value in column.items():
            grid[account][period] = value

    COL_ACCOUNT = 48
    COL_PERIOD = 14

    headers = [f'{x:>{COL_PERIOD}}' for x in periods]
    report = f"{' ' * COL_ACCOUNT}{''.join(headers)}\n"
    for account in sorted(all_accounts):
        values = [util.get_plain_amount(
            grid[account].get(x, 0),
            colwidth=COL_PERIOD
        ) for x in periods]
        report += f"{account:{COL_ACCOUNT}}{''.join(values)}\n"

    dashes = [f"{'-' * (COL_PERIOD - 2):>{COL_PERIOD}}" for x in periods]
    report += f"{' ' * COL_ACCOUNT}{''.join(dashes)}\n"
    totals = [util.get_plain_amount(
        sum(all_periods[x].values()),
        colwidth=COL_PERIOD
    ) for x in periods]
    report += f"{' ' * COL_ACCOUNT}{''.join(totals)}\n"

    # print('all_periods:')
    # pprint(all_periods)
    # print('\ngrid:')
    # pprint(grid)
    return report


def get_included_periods(args, ledger_args, unit='year'):
    # --collapse behavior seems suspicous, but --empty
    # appears to work for our purposes here
    # groups.google.com/forum/?fromgroups=#!topic/ledger-cli/HAKAMYiaL7w
    begin = ['-b', args.begin] if args.begin else []
    end = ['-e', args.end] if args.end else []
    period = ['-p', args.period] if args.period else []

    if unit == 'year':
        period_options = ['--yearly', '-y', '%Y']
        period_len = 4
    else:  # month
        period_options = ['--monthly', '-y', '%Y/%m']
        period_len = 7

    lines = get_ledger_output([
        'reg'
    ] + begin + end + period + period_options + [
        '--collapse',
        '--empty'
    ] + ledger_args).split('\n')

    return {x[:period_len] for x in lines if x[:period_len].strip() != ''}


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
        amount = float(match.groups()[DOLLARS].replace(',', ''))  # todo: test
        column[match.groups()[ACCOUNT]] = amount

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
    parser.add_argument(
        '-l', '--ledger',
        type=str,
        help='ledgerbil passthrough'
    )

    # workaround for problems with nargs=argparse.REMAINDER
    # see: https://bugs.python.org/issue17050
    return parser.parse_known_args(args)


def main(argv=[]):
    args, ledger_args = get_args(argv)
    if args.ledger:
        options = shlex.split(args.ledger)
        print(get_ledger_output(options))
        print(' '.join(get_ledger_command(options)))
        return

    print(get_grid_report(args, ledger_args))
