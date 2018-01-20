import argparse
import json
import re

from .colorable import Colorable
from .settings import Settings
from .util import get_colored_amount

settings = Settings()


def get_portfolio_report(args):
    data = get_portfolio_data()
    report = f''
    for account in data:
        account_name = account['account']
        if not re.search(args.accounts_regex, account_name):
            continue

        if args.history:
            report += f'{get_account_history(account)}\n'
        else:
            report += 'todo: not history\n'

    if not report:
        report = 'No accounts matched {}'.format(args.accounts_regex)

    return report


def get_account_history(account):
    labels = f"labels: {', '.join(account['labels'])}"
    history = '{account}\n{label}'.format(
        account=Colorable('purple', account['account']),
        label=Colorable('white', labels, '>75') if account['labels'] else ''
    )

    years = account['years']
    if len(years):
        header = (f"\n    year  {'contrib':>10}  {'shares':>9}  "
                  f"{'price':>10}  {'value':>14}  {'+/-':>14}\n")
        history += f"{Colorable('cyan', header)}"

    previous_year_value = None
    diff_f = ''
    for year in sorted(years):
        contributions = f"$ {years[year]['contributions']['total']:,.0f}"
        contributions_f = Colorable('yellow', contributions, '>10')

        shares = years[year]['shares']
        shares_f = Colorable('blue', shares, '9,.0f')

        price = years[year]['price']
        price_f = f'$ {price:,.2f}'

        value = shares * price
        value_f = get_colored_amount(value, 14)

        if previous_year_value:
            diff_f = get_colored_amount(value - previous_year_value, 14)

        history += (f'    {year}  {contributions_f}  {shares_f}  '
                    f'{price_f:>10}  {value_f:>14}  {diff_f}\n')

        previous_year_value = value

    return history


def get_portfolio_data():
    # todo: handle bad file or data
    with open(settings.PORTFOLIO_FILE, 'r') as portfile:
        return json.loads(portfile.read())


def get_args(args=[]):
    parser = argparse.ArgumentParser(
        prog='ledgerbil/main.py portfolio',
        formatter_class=(
            lambda prog: argparse.HelpFormatter(prog, max_help_position=36)
        )
    )
    parser.add_argument(
        '-a', '--accounts',
        type=str,
        dest='accounts_regex',
        default='.*',
        help='include accounts that match this regex, default = .* (all)'
    )
    parser.add_argument(
        '-H', '--history',
        action='store_true',
        help='show account history'
    )

    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    print(get_portfolio_report(args))
