import argparse
import re
from collections import defaultdict
from datetime import date
from textwrap import dedent

from .. import util
from ..colorable import Colorable
from .runner import get_ledger_output

SORT_DEFAULT = 'total'
ACCOUNT_LINE_REGEX = re.compile(r'^\s*(?:\$ (-?[\d,.]+|0(?=  )))\s*(.*)$')
PAYEE_SUBTOTAL_REGEX = re.compile(r'^.*?\$ (\S+)\s*\$.*$')


def get_grid_report(args, ledger_args=[]):
    unit = 'month' if args.month else 'year'
    period_names, current_period_name = get_period_names(
        args,
        ledger_args,
        unit
    )
    if not period_names:
        return ''

    # row headers: i.e. accounts or payees
    row_headers, columns = get_columns(
        period_names,
        ledger_args,
        depth=args.depth,
        current=current_period_name,
        payee=args.payee
    )
    rows = get_rows(row_headers, columns, period_names, args.sort, args.limit)
    return get_flat_report(rows)


def get_flat_report(rows):
    FMT_PERIOD = 14
    ROW_HEADER = -1
    ROW_TOTAL = -2
    DATA_START = 1
    DATA_END = -1
    COL_HEADER = 0
    COL_TOTAL = -1

    headers = [f'{pn:>{FMT_PERIOD}}' for pn in rows[COL_HEADER]]
    report = f"{Colorable('white', ''.join(headers))}\n"

    for row in rows[DATA_START:DATA_END]:
        row_header_f = Colorable('blue', row[ROW_HEADER])
        amounts_f = [util.get_colored_amount(
            amount,
            colwidth=FMT_PERIOD,
            positive='yellow',
            zero='grey'
        ) for amount in row[:ROW_TOTAL]]
        row_total_f = util.get_colored_amount(
            row[ROW_TOTAL],
            colwidth=FMT_PERIOD
        )
        report += f"{''.join(amounts_f)}{row_total_f}  {row_header_f}\n"

    dashes = [
        f"{'-' * (FMT_PERIOD - 2):>{FMT_PERIOD}}" for x in rows[COL_TOTAL]
    ]
    col_totals_f = [
        util.get_colored_amount(t, FMT_PERIOD) for t in rows[COL_TOTAL]
    ]
    report += f"{Colorable('white', ''.join(dashes))}\n"
    report += f"{''.join(col_totals_f)}\n"
    return report


def get_period_names(args, ledger_args, unit='year'):
    # --collapse behavior seems suspicous, but --empty
    # appears to work for our purposes here
    # groups.google.com/forum/?fromgroups=#!topic/ledger-cli/HAKAMYiaL7w
    begin = ['--begin', args.begin] if args.begin else []
    end = ['--end', args.end] if args.end else []
    period = ['--period', args.period] if args.period else []

    if unit == 'year':
        date_format = '%Y'
        period_options = ['--yearly', '--date-format', date_format]
        period_len = 4
    else:
        date_format = '%Y/%m'
        period_options = ['--monthly', '--date-format', date_format]
        period_len = 7

    lines = get_ledger_output([
        'register'
    ] + begin + end + period + period_options + [
        '--collapse',
        '--empty'
    ] + ledger_args).split('\n')

    names = sorted(
        {x[:period_len] for x in lines if x[:period_len].strip() != ''}
    )

    current_period_name = None
    if args.current:
        current_period_date = date.today().strftime(date_format)
        if current_period_date in names:
            current_period_name = current_period_date
            # remove future periods
            names = names[:names.index(current_period_date) + 1]

    return names, current_period_name


def get_columns(period_names, ledger_args, depth=0, current=None, payee=False):
    row_headers = set()
    columns = {}
    for period_name in period_names:
        if current and current == period_name:
            ledger_args += ['--end', 'tomorrow']

        if payee:
            column = get_column_payees(['--period', period_name] + ledger_args)
        else:
            column = get_column_accounts(
                ['--period', period_name] + ledger_args,
                depth
            )

        row_headers.update(column.keys())
        columns[period_name] = column

    return row_headers, columns


def get_column_accounts(ledger_args, depth=0):
    ACCOUNT = 1
    DOLLARS = 0

    lines = get_ledger_output(['balance', '--flat'] + ledger_args).split('\n')
    column = defaultdict(int)
    for line in lines:
        if line == '' or line[0] == '-':
            break
        match = re.match(ACCOUNT_LINE_REGEX, line)
        # should match as long as --market is used?
        assert match, f'Account line regex did not match: {line}'
        amount = float(match.groups()[DOLLARS].replace(',', ''))
        account = match.groups()[ACCOUNT]
        if depth > 0:
            account_parts = account.split(':')
            account = ':'.join(account_parts[:depth])
        column[account] += amount

    return column


def get_column_payees(ledger_args):
    DOLLARS = 0
    lines = get_ledger_output(
        ['register', 'expenses', '--group-by', '(payee)',
         '--collapse', '--subtotal', '--depth', '1'] + ledger_args
    ).split('\n')
    column = {}
    payee = None
    for line in lines:
        if not line:
            continue
        if not payee:
            payee = line
        else:
            match = re.match(PAYEE_SUBTOTAL_REGEX, line)
            assert match, f'Payee subtotal regex did not match: {line}'
            assert payee not in column, f'Payee already in column: {payee}'
            amount = float(match.groups()[DOLLARS].replace(',', ''))
            column[payee] = amount
            payee = None

    return column


def get_rows(row_headers, columns, period_names, sort=SORT_DEFAULT, limit=0):
    if len(period_names) == 1:
        has_total_column = False
        if sort == SORT_DEFAULT:
            sort = period_names[0]
    else:
        has_total_column = True

    grid = get_grid(row_headers, columns)

    rows = []
    for row_header in row_headers:
        amounts = [grid[row_header].get(pn, 0) for pn in period_names]
        if has_total_column:
            rows.append(tuple(amounts + [sum(amounts)] + [row_header]))
        else:
            rows.append(tuple(amounts + [row_header]))

    if sort == 'row':
        sort_index = len(period_names) + 1
        reverse_sort = False
    elif sort in period_names:
        sort_index = period_names.index(sort)
        reverse_sort = True
    else:
        # SORT_DEFAULT (or anything that falls through)
        sort_index = len(period_names)
        reverse_sort = True

    rows = sorted(rows, key=lambda x: x[sort_index], reverse=reverse_sort)
    if limit > 0:
        rows = rows[:limit]

    headers = period_names
    if has_total_column:
        headers.append(SORT_DEFAULT)

    totals = tuple(sum(x) for x in list(zip(*rows))[:-1])

    return [tuple(headers)] + rows + [totals]


def get_grid(row_headers, columns):
    grid = {key: {} for key in row_headers}
    for period_name, column in columns.items():
        for row_header, amount in column.items():
            grid[row_header][period_name] = amount

    return grid


def get_args(args=[]):
    program = 'ledgerbil/main.py grid'
    description = dedent('''\
        Show ledger balance report in tabular form with years or months as the
        columns. Begin, end, and period params are handled as ledger interprets
        them, and all arguments not defined here are passed through to ledger.

        Don't specify bal, balance, reg, or register!

        e.g. ./main.py expenses -p 'last 2 years' will show expenses for last
        two years with separate columns for the years.

        Currently supports ledger --flat reports. (Although you don't have to
        specify --flat.)

        Payee reports will also pass through ledger arguments, but currently
        they assume "expenses" and if you wanted to further constraint that
        you would need to do something like "and @^a" to get only payees
        starting with a.
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
        '--current',
        action='store_true',
        default=False,
        help='exclude future transactions'
    )
    parser.add_argument(
        '--depth',
        type=int,
        metavar='N',
        default=0,
        help='limit the depth of account tree for account reports'
    )
    parser.add_argument(
        '--payee',
        action='store_true',
        default=False,
        help='show expenses by payee'
    )
    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        default=0,
        help='limit the number of rows shown to top N'
    )
    # todo: total only (in particular wanted for payees)
    parser.add_argument(
        '-s', '--sort',
        type=str,
        default=SORT_DEFAULT,
        help='sort by specified column header, or "row" to sort\nby account '
             'or payee (default by total)'
    )

    # workaround for problems with nargs=argparse.REMAINDER
    # see: https://bugs.python.org/issue17050
    return parser.parse_known_args(args)


def main(argv=[]):
    args, ledger_args = get_args(argv)
    print(get_grid_report(args, ledger_args))
