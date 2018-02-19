import argparse
import re
import shlex
from pprint import pprint

from .runner import get_ledger_command, get_ledger_output

LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')


def get_grid_report(args, ledger_args=[]):
    unit = 'month' if args.month else 'year'
    periods = get_included_periods(args, ledger_args, unit)

    all_accounts = set()
    all_periods = {}
    for period in periods:
        column = get_column(['bal', '--flat', '-p', period] + ledger_args)
        all_accounts.update(column.keys())
        all_periods[period] = column

    pprint(all_periods)
    return all_accounts


def get_included_periods(args, ledger_args, unit='year'):
    # --collapse behavior seems suspicous, but --empty
    # appears to work for our purposes here
    # groups.google.com/forum/?fromgroups=#!topic/ledger-cli/HAKAMYiaL7w
    begin = ['-b', args.begin] if args.begin else []
    end = ['-e', args.end] if args.end else []
    period = ['-p', args.period] if args.period else []

    if unit == 'year':
        options = ['--yearly', '-y', '%Y']
        period_len = 4
    else:  # month
        options = ['--monthly', '-y', '%Y/%m']
        period_len = 7

    lines = get_ledger_output([
        'reg'
    ] + begin + end + period + options + [
        '--collapse',
        '--empty'
    ] + ledger_args).split('\n')

    return {x[:period_len] for x in lines if x}


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
        help='begin date'
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

    pprint(get_grid_report(args, ledger_args))
