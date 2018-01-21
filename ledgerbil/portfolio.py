import argparse
import json
import re
from collections import defaultdict

from .colorable import Colorable
from .settings import Settings
from .util import get_colored_amount

settings = Settings()


def get_portfolio_report(args):
    data = get_portfolio_data()
    report = ''
    included_years = set()
    matched = []
    for account in data:
        account_name = account['account']
        if not re.search(args.accounts_regex, account_name):
            continue

        if args.history:
            report += f'{get_account_history(account)}\n'
        else:
            # todo: validate years?
            included_years.update(set(account['years'].keys()))
            matched.append(account)

    if not report and not matched:
        report = 'No accounts matched {}'.format(args.accounts_regex)

    if matched:
        included_years = [int(year) for year in included_years]
        year_range = (min(included_years), max(included_years))
        report = get_performance_report(matched, year_range)
        matched_names = [account['account'] for account in matched]
        report += '\n'.join(matched_names)
        report += f'\n{year_range}\n'

    return report


def get_performance_report(accounts, year_range):
    years = add_up_yearly_numbers(accounts, year_range)
    return temp_perf_report(years)


def add_up_yearly_numbers(accounts, year_range):
    years = defaultdict(lambda: defaultdict(float))
    for account in accounts:
        previous_value = 0
        for year in range(year_range[0], year_range[1] + 1):
            if str(year) not in account['years'].keys():
                if previous_value:
                    # todo: integration with ledger to get current value
                    years[year]['value'] += previous_value
                continue

            data = account['years'][str(year)]
            contrib_total = data['contributions']['total']
            modifier = data['contributions']['modifier']
            contrib_start = contrib_total * modifier
            value = data['price'] * data['shares']

            years[year]['contrib_start'] += contrib_start
            years[year]['contrib_end'] += (contrib_total - contrib_start)
            years[year]['value'] += value

            previous_value = value

    return years


def temp_perf_report(years):
    report = f"year  {'contrib':>12}  {'value':>16}\n"
    for year in sorted(years):
        contributions = get_colored_amount(
            years[year]['contrib_start'] + years[year]['contrib_end'],
            column_width=12
        )
        value = get_colored_amount(years[year]['value'], column_width=16)
        report += f'{year}  {contributions}  {value}\n'

    return report


def get_account_history(account):
    labels = f"labels: {', '.join(account['labels'])}"
    history = '{account}\n{label}'.format(
        account=Colorable('purple', account['account']),
        label=Colorable('white', labels, '>72') if account['labels'] else ''
    )

    years = account['years']
    if len(years):
        header = (f"\n    year  {'contrib':>10}  {'shares':>9}  "
                  f"{'price':>10}  {'value':>12}  {'+/-':>13}\n")
        history += f"{Colorable('cyan', header)}"

    # todo: use years min and max and account for "missing" years...

    contributions_total = 0
    previous_year_value = None
    diff_f = ''
    for year in sorted(years):
        contributions = years[year]['contributions']['total']
        contributions_f = Colorable('yellow', f'$ {contributions:,.0f}', '>10')

        shares = years[year]['shares']
        shares_f = Colorable('blue', shares, '9,.0f')

        price = years[year]['price']
        price_f = f'$ {price:,.2f}'

        value = shares * price
        value_f = get_colored_amount(value, column_width=12, decimals=0)

        if previous_year_value:
            diff_f = get_colored_amount(
                value - previous_year_value,
                column_width=13,
                decimals=0
            )

        history += (f'    {year}  {contributions_f}  {shares_f}  '
                    f'{price_f:>10}  {value_f:>12}  {diff_f}\n')

        previous_year_value = value
        contributions_total += contributions

    if len(years) and contributions_total:
        history += '          {}\n'.format(
            get_colored_amount(contributions_total, 10, decimals=0)
        )

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
