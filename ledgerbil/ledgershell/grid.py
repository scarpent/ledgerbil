import argparse
import csv
import re
import sys
from collections import defaultdict
from concurrent import futures
from datetime import date
from io import StringIO
from textwrap import dedent

from dateutil.relativedelta import relativedelta

from .. import util
from ..colorable import Colorable
from ..settings_getter import get_setting
from ..util import get_date, parse_args
from .runner import get_ledger_output
from .util import get_account_balance, get_first_dollar_amount_float, get_payee_subtotal

TOTAL_HEADER = "Total"
SORT_DEFAULT = TOTAL_HEADER.lower()
EMPTY_VALUE = ""


def get_grid_report(args, ledger_args):
    unit = "month" if args.month else "year"
    period_names, current_period = get_period_names(args, ledger_args, unit)
    if not period_names:
        return ""

    # Row headers: i.e. accounts, payees, net worth (things with amounts)
    row_headers, columns = get_columns(args, ledger_args, period_names, current_period)
    # Many queries with no results will come up empty on period names and
    # return above, but some, for example queries with "and" in them, may not
    if not row_headers:
        return ""

    rows = get_rows(
        row_headers,
        columns,
        period_names,
        args.sort,
        args.limit_rows,
        args.total_only,
        no_total=args.networth,
    )

    # Move account/payee name to first column for csv and/or transpose
    #  - Makes more sense for csv/spreadsheet
    #  - Positions for move to top in transpose
    #  - But we'll move back to right side for transposed flat report to
    #    avoid a bunch of complications from handling differently there
    if args.csv or args.transpose:
        for row in rows:
            row.insert(0, row.pop())

    if args.transpose:
        rows = list(map(list, zip(*rows)))

    if args.csv:
        return get_csv_report(rows, tabs=args.tab)

    if args.transpose:
        # Move account/payee back to the right side
        for row in rows:
            row.append(row.pop(0))

    return get_flat_report(rows, networth=args.networth)


def get_csv_report(rows, tabs=False):
    delimiter = "\t" if tabs else ","
    output = StringIO()
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def get_flat_report(rows, networth=False):
    # 2 columns means has a single data column and account/payee column;
    # will have 4 or more columns otherwise, and have a total column;
    # same deal for total row; however! note that we sneak in --total-only
    # as if a regular single column (is also highlighted as a non-total col)
    has_total_column = len(rows[0]) > 3 and not networth
    has_total_row = len(rows) > 3 and not networth

    AMOUNT_WIDTH = 14  # width of columns with amounts
    ACCOUNT_PAYEE_COLUMN = -1  # last column, aka row header
    TOTAL_COLUMN = -2  # second to last column (*if* we have a total)
    AMOUNT_COLUMN_START = 0  # inclusive
    if has_total_column:
        AMOUNT_COLUMN_END = TOTAL_COLUMN  # exclusive
    else:
        AMOUNT_COLUMN_END = ACCOUNT_PAYEE_COLUMN  # exclusive

    DATA_ROW_START = 1
    DATA_ROW_END = -1 if has_total_row else len(rows)  # exclusive
    HEADER_ROW = 0
    FOOTER_ROW = -1 if has_total_row else None

    headers = get_flat_report_header(
        rows[HEADER_ROW][:ACCOUNT_PAYEE_COLUMN], AMOUNT_WIDTH
    )
    report = str(Colorable("white", headers))

    for row in rows[DATA_ROW_START:DATA_ROW_END]:
        row_header_f = Colorable("blue", row[ACCOUNT_PAYEE_COLUMN])
        amounts_f = [
            util.get_colored_amount(
                amount, colwidth=AMOUNT_WIDTH, positive="yellow", zero="grey"
            )
            for amount in row[AMOUNT_COLUMN_START:AMOUNT_COLUMN_END]
        ]

        if has_total_column:
            row_total_f = util.get_colored_amount(
                row[TOTAL_COLUMN], colwidth=AMOUNT_WIDTH
            )
        else:
            row_total_f = ""

        report += f"{''.join(amounts_f)}{row_total_f}  {row_header_f}\n"

    if not has_total_row:
        return report

    footers = rows[FOOTER_ROW][:ACCOUNT_PAYEE_COLUMN]
    dashes = [f"{'-' * (AMOUNT_WIDTH - 2):>{AMOUNT_WIDTH}}" for x in footers]
    footers_f = [util.get_colored_amount(t, AMOUNT_WIDTH) for t in footers]
    report += f"{Colorable('white', ''.join(dashes))}\n"
    report += f"{''.join(footers_f)}\n"

    return report


def get_flat_report_header(headers, width=14):
    header_lists = get_flat_report_header_lists(headers, width)
    report_header = ""
    for i in range(len(header_lists[0])):
        row = [line[i] for line in header_lists]
        headers_f = [f"{header:>{width}}" for header in row]
        report_header += f"{''.join(headers_f)}\n"

    return report_header


def get_flat_report_header_lists(headers, width=14):
    """Attempts to break up account and payee names into chunks that
    will read better when they are used as column headers"""

    TRUNC_CHAR = "~"
    ACCOUNT_TYPES = ["assets:", "liabilities:", "income:", "expenses:", "equity:"]
    HEADER_SPLIT = r"(?<=: )|(?<=:)(?=\S)|(?<=[- ])"
    padded_width = width - 3 if width >= 14 else width - 1

    header_lists = []
    for header in headers:
        the_header = []
        row_in_progress = []

        parts = re.split(HEADER_SPLIT, header)
        if parts[0].strip().lower() in ACCOUNT_TYPES:
            # would like the top level account types to live on their own row
            first_part = parts.pop(0).strip()
            if len(first_part) > padded_width:
                first_part = f"{first_part[:padded_width - 1]}{TRUNC_CHAR}"
            the_header.append(first_part)

        for part in parts:
            if len("".join(row_in_progress + [part.rstrip()])) <= padded_width:
                row_in_progress.append(part)
            else:
                if row_in_progress:
                    the_header.append("".join(row_in_progress).strip())
                if len(part.rstrip()) > padded_width:
                    part = f"{part[:padded_width - 1]}{TRUNC_CHAR}"
                row_in_progress = [part]

        the_header.append("".join(row_in_progress).strip())

        header_lists.append(the_header)

    # pad header row lists so they're all the same length
    longest_list = max(len(hlist) for hlist in header_lists)
    for header_list in header_lists:
        for _ in range(longest_list - len(header_list)):
            header_list.insert(0, "")

    return header_lists


def get_period_names(args, ledger_args, unit="year"):
    # --collapse behavior seems suspicous, but with --empty
    # appears to work for our purposes here
    # groups.google.com/forum/?fromgroups=#!topic/ledger-cli/HAKAMYiaL7w
    begin = ("--begin", args.begin) if args.begin else ()
    end = ("--end", args.end) if args.end else ()
    period = ("--period", args.period) if args.period else ()

    if unit == "year":
        date_format = get_setting("DATE_FORMAT_YEAR")
        period_options = ("--yearly", "--date-format", date_format)
        period_len = 4
    else:
        date_format = get_setting("DATE_FORMAT_MONTH")
        period_options = ("--monthly", "--date-format", date_format)
        period_len = 7

    lines = get_ledger_output(
        ("register",)
        + begin
        + end
        + period
        + period_options
        + ("--collapse", "--empty")
        + ledger_args
    ).split("\n")

    names = sorted({x[:period_len] for x in lines if x[:period_len].strip() != ""})

    current_period = None
    if args.current:
        current_period_date_str = date.today().strftime(date_format)
        if current_period_date_str in names:
            current_period = current_period_date_str
            # remove future periods
            names = names[: names.index(current_period_date_str) + 1]

    return tuple(names), current_period


def get_columns(args, ledger_args, period_names, current_period=None):

    with futures.ThreadPoolExecutor(max_workers=50) as executor:
        to_do = []
        ending = ()
        for period_name in period_names:
            if current_period and current_period == period_name:
                ending = ("--end", "tomorrow")

            future = executor.submit(get_column, args, ledger_args, period_name, ending)
            to_do.append(future)

        row_headers = set()
        columns = {}
        for future in futures.as_completed(to_do):
            period_name, column = future.result()
            row_headers.update(column.keys())
            columns[period_name] = column

    return row_headers, columns


def get_column(args, ledger_args, period_name, ending):
    if args.payees:
        column = get_column_payees(period_name, ledger_args + ending)
    elif args.networth:
        networth_period = "tomorrow" if ending else period_name
        column = get_column_networth(networth_period, ledger_args)
    else:
        column = get_column_accounts(period_name, ledger_args + ending, args.depth)

    return period_name, column


def get_column_accounts(period_name, ledger_args, depth=0):
    lines = get_ledger_output(
        ("balance", "--flat", "--period", period_name) + ledger_args
    ).split("\n")
    column = defaultdict(int)
    next_is_total = False

    for line in lines:

        if next_is_total:
            validate_column_total(
                period_name,
                column_total=sum(column.values()),
                ledgers_total=util.get_float(line),
            )
            break
        elif line and line[0] == "-":  # ledger's total line separator
            next_is_total = True
            continue
        elif line == "":  # last element when ledger doesn't give a total
            break

        balance = get_account_balance(line)
        # should match as long as --market is used?
        assert balance, f"Did not find expected account and dollars: {line}"
        account = balance.account
        if depth > 0:
            account_parts = balance.account.split(":")
            account = ":".join(account_parts[:depth])
        column[account] += balance.amount

    return column


def validate_column_total(period_name, column_total=0, ledgers_total=0):
    # Ledger has an unfortunate way of reporting things with --flat, when
    # funds are applied to both parent and child account. It appears to
    # double count them in line items but not in the total.

    # In the column total, which is "our" total and what will be shown in
    # the report, we will get the wrong sum. Let's warn when this happens.
    # (Which means ledgerbil's stance is that you really shouldn't use
    # your accounts this way.)

    # We'll not concern ourselves over small floating point differences
    if round(abs(column_total - ledgers_total), 2) > 0.05:
        warn_column_total(period_name, column_total, ledgers_total)


def warn_column_total(period_name, column_total=0, ledgers_total=0):
    message = (
        f"Warning: Differing total found between ledger's {ledgers_total} "
        f"and ledgerbil's {column_total} for --period {period_name}. "
        "Ledger's will be the correct total. This is mostly likely caused "
        "by funds being applied to both a parent and child account."
    )
    print(message, file=sys.stderr)


def get_column_payees(period_name, ledger_args):
    lines = get_ledger_output(
        (
            "register",
            "--group-by",
            "(payee)",
            "--collapse",
            "--subtotal",
            "--depth",
            "1",
            "--period",
            period_name,
        )
        + ledger_args
    ).split("\n")
    column = {}
    payee = None
    for line in lines:
        if not line:
            continue
        if not payee:
            payee = line
        else:
            amount = get_payee_subtotal(line)
            assert amount is not None, f"Did not find expected payee subtotal: {line}"
            assert payee not in column, f"Payee already in column: {payee}"
            column[payee] = amount
            payee = None

    return column


def get_column_networth(period_name, ledger_args):
    if period_name == "tomorrow":
        ending = period_name
    else:
        if len(period_name) == 4:  # year
            date_format = get_setting("DATE_FORMAT_YEAR")
            networth_relativedelta = relativedelta(years=1)
        else:  # month
            date_format = get_setting("DATE_FORMAT_MONTH")
            networth_relativedelta = relativedelta(months=1)

        # Let's report net worth for the end of the current period,
        # which means we want to use the next period as the ending
        # since `--end` is the "exclusive" end
        period_date = get_date(period_name, date_format)
        next_period_date = period_date + networth_relativedelta
        ending = next_period_date.strftime(date_format)

    accounts = tuple(parse_args(get_setting("NETWORTH_ACCOUNTS")))
    lines = get_ledger_output(
        ("balance",) + accounts + ("--depth", "1", "--end", ending) + ledger_args
    ).split("\n")

    amount = lines[-1].strip()
    if amount:
        networth = get_first_dollar_amount_float(amount)
    else:
        networth = 0

    column = {"net worth": networth}
    return column


def get_rows(
    row_headers,
    columns,
    period_names,
    sort=SORT_DEFAULT,
    limit_rows=0,
    total_only=False,
    no_total=False,
):

    ACCOUNT_PAYEE_HEADER = EMPTY_VALUE
    ACCOUNT_PAYEE_COLUMN = -1
    TOTAL_COLUMN = -2

    grid = get_grid(row_headers, columns)

    rows = []
    for row_header in row_headers:
        amounts = [grid[row_header].get(pn, 0) for pn in period_names]
        rows.append(amounts + [sum(amounts)] + [row_header])

    if sort == "row":
        sort_index = ACCOUNT_PAYEE_COLUMN
        reverse_sort = False
    elif sort in period_names:
        sort_index = period_names.index(sort)
        reverse_sort = True
    else:
        # SORT_DEFAULT (or anything that falls through)
        sort_index = len(period_names)
        reverse_sort = True

    rows = sorted(rows, key=lambda x: x[sort_index], reverse=reverse_sort)
    if limit_rows > 0:
        rows = rows[:limit_rows]

    if len(rows) > 1:
        totals = [sum(x) for x in list(zip(*rows))[:ACCOUNT_PAYEE_COLUMN]]
        # was somehow getting test values like this 5.861977570020827e-14,
        # instead of expected 0.0, so we'll fiddle a bit...
        epsilon = 1e-10
        totals = [
            (
                float(f"{total:.2f}".rstrip("0").rstrip("."))
                if abs(total) >= epsilon
                else 0.0
            )
            for total in totals
        ]
        rows += [totals + [TOTAL_HEADER]]

    headers = period_names + (TOTAL_HEADER, ACCOUNT_PAYEE_HEADER)
    rows = [list(headers)] + rows

    if total_only:
        new_rows = []
        for row in rows:
            new_rows.append(row[-2:])
        return new_rows

    if no_total or len(period_names) == 1:
        for row in rows:
            del row[TOTAL_COLUMN]

    return rows


def get_grid(row_headers, columns):
    grid = {key: {} for key in row_headers}
    for period_name, column in columns.items():
        for row_header, amount in column.items():
            grid[row_header][period_name] = amount

    return grid


def get_args(args):
    program = "ledgerbil/main.py grid"
    description = dedent(
        """\
        Show ledger balance report in tabular form with years or months as the
        columns. Begin, end, and period params are handled as ledger interprets
        them, and all arguments not defined here are passed through to ledger.

        Don't specify bal, balance, reg, or register!

        e.g. ./main.py grid expenses -p 'last 2 years' will show expenses for
        last two years with separate columns for the years.

        Begin and end dates only determine the range for which periods will be
        reported. They do not limit included entries within a period. For
        example, with --year periods, specifying --end 2018/07/01 will cause
        all of 2018 to be included.

        Currently supports ledger --flat reports. (Although you don't specify
        --flat.)

        Payee reports will also pass through ledger arguments. It is best to
        specify an account to constrain the query, e.g. expenses. If not given
        any accounts, ledger gives odd results for the query used by ledgerbil:

        register --group-by '(payee)' --collapse --subtotal --depth 1
    """
    )
    parser = argparse.ArgumentParser(
        prog=program,
        description=description,
        allow_abbrev=False,
        formatter_class=(
            lambda prog: argparse.RawDescriptionHelpFormatter(
                prog, max_help_position=40
            )
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-y", "--year", action="store_true", default=True, help="year grid (default)"
    )
    group.add_argument("-m", "--month", action="store_true", help="month grid")
    parser.add_argument("-b", "--begin", type=str, metavar="DATE", help="begin date")
    parser.add_argument("-e", "--end", type=str, metavar="DATE", help="end date")
    parser.add_argument("-p", "--period", type=str, help="period expression")
    parser.add_argument(
        "--current",
        action="store_true",
        default=False,
        help="exclude future transactions",
    )
    parser.add_argument(
        "--depth",
        type=int,
        metavar="N",
        default=0,
        help="limit the depth of account tree for account reports",
    )
    parser.add_argument(
        "--payees",
        action="store_true",
        default=False,
        help=(
            "show results by payee (results may be nonsensical "
            "if you do not specify accounts, e.g. expenses)"
        ),
    )
    parser.add_argument(
        "--net-worth",
        dest="networth",
        action="store_true",
        default=False,
        help="show net worth at end of periods",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        metavar="N",
        default=0,
        help="limit the number of rows shown to top N",
    )
    parser.add_argument(
        "-T",
        "--total-only",
        action="store_true",
        default=False,
        help="show only the total column",
    )
    parser.add_argument(
        "-s",
        "--sort",
        type=str,
        default=SORT_DEFAULT,
        help=(
            'sort by specified column header, or "row" to sort '
            "by account or payee (default: by total)"
        ),
    )
    # note the departure here with store_false and default True; seemed easier
    # to essentially change the default this way and then just update breaking
    # tests appropriately, although they weren't renamed so things might be a
    # *bit* confusing...
    parser.add_argument(
        "-t",
        "--transpose",
        action="store_false",
        default=True,
        help="transpose columns and rows",
    )
    parser.add_argument(
        "--csv", action="store_true", default=False, help="output as csv"
    )
    parser.add_argument(
        "--tab",
        action="store_true",
        default=False,
        help="output as tsv (tab-delimited)",
    )
    parser.add_argument(
        "--no-color", action="store_true", default=False, help="output without color"
    )

    # workaround for problems with nargs=argparse.REMAINDER
    # see: https://bugs.python.org/issue17050
    args, ledger_args = parser.parse_known_args(args)
    if args.tab and not args.csv:
        args.csv = True
    return args, tuple(ledger_args)


def main(argv=None):
    args, ledger_args = get_args(argv or [])

    report = get_grid_report(args, ledger_args)

    if args.no_color and not args.csv:
        report = Colorable.get_plain_string(report)

    print(report, end="")
