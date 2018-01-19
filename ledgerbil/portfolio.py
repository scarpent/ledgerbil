import argparse
import json
import re

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
        report += f'\n{account_name}\n'
        report += f'{get_account_history(account)}\n'

    if not report:
        report = 'No accounts matched {}'.format(args.accounts_regex)

    return report


def get_account_history(account):
    history = f"labels: {', '.join(account['labels'])}\n"

    years = account['years']
    if len(years):
        history += f"\tyear  {'contributions':15}{'shares':>10}  {'price':>10}  {'value':>14}  {'+/-':>14}\n"  # noqa

    previous_year_value = None
    diff_f = ''
    for year in sorted(years):
        contributions = f"$ {years[year]['contributions']['total']:,.0f}"
        shares = years[year]['shares']
        price = years[year]['price']
        price_f = f'$ {price:,.2f}'
        value = shares * price
        value_f = f'$ {value:,.0f}'
        if previous_year_value:
            diff = value - previous_year_value
            diff_f = f'$ {diff:,.0f}'
            diff_f = get_colored_amount(value - previous_year_value, 14)
        history += f'\t{year}  {contributions:>13}  {shares:>10,}  {price_f:>10}  {value_f:>14}  {diff_f}\n'  # noqa

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

    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    print(get_portfolio_report(args))
