import argparse
import json
import re
from collections import defaultdict, namedtuple

from . import util
from .colorable import Colorable
from .settings import Settings

settings = Settings()

Year = namedtuple('Year', 'year contributions value gain gain_value')


def get_portfolio_report(args):
    matched, included_years = get_matching_accounts(args.accounts_regex)

    if not matched:
        return 'No accounts matched {}'.format(args.accounts_regex)

    if args.history:
        report = get_history_report(matched)
    else:
        report = get_performance_report(matched, included_years)

    return report


def get_matching_accounts(accounts_regex):
    portfolio_data = get_portfolio_data()
    included_years = set()
    matched = []
    for account in portfolio_data:
        account_name = account['account']
        if not re.search(accounts_regex, account_name):
            continue

        # todo: validation?
        #       - year: format and sanity check on range
        #       - warn if missing years in accounts?
        included_years.update(set(account['years'].keys()))
        matched.append(account)

    return matched, included_years


def get_performance_report(accounts, included_years):
    year_start, year_end = util.get_start_and_end_range(included_years)
    totals = get_yearly_combined_accounts(accounts, year_start, year_end)
    years = get_yearly_with_gains(totals)
    info = f"{len(accounts)} account{'' if len(accounts) == 1 else 's'}: "
    info += ', '.join([account['account'] for account in accounts[:2]])
    if len(accounts) > 2:
        info += ', ...'
    return '{info}\n\n{report}'.format(
        info=re.sub('(?i)assets: ?', '', info),
        report=temp_perf_report(years)
    )


def temp_perf_report(years):
    report = (f"year  {'contrib':>12}  {'value':>12}  "
              f"{'gain %':>7}  {'gain val':>12}\n")
    for year in years:
        contrib = util.get_plain_dollar_amount(
            year.contributions, 12,
            decimals=0
        )
        value = util.get_plain_dollar_amount(year.value, 12, decimals=0)
        gain = '' if year.gain == 1 else f'{(year.gain - 1) * 100:.2f}'
        if year.gain == 1:
            gain_value = f'{"":>12}'
        else:
            gain_value = util.get_colored_amount(
                year.gain_value,
                12,
                decimals=0
            )

        report += (f'{year.year}  {contrib}  {value}  {gain:>7}  '
                   f'{gain_value}\n')

    return report


def get_yearly_combined_accounts(accounts, year_start, year_end):
    # Combine all the accounts into total contributions and value per year
    totals = defaultdict(lambda: defaultdict(float))
    for account in accounts:
        previous_value = 0
        for year in range(year_start, year_end):
            if str(year) not in account['years'].keys():
                if previous_value:
                    # todo: integration with ledger to get current info
                    totals[year]['contributions'] += 0
                    totals[year]['value'] += previous_value
                continue

            data = account['years'][str(year)]
            value = data['price'] * data['shares']

            totals[year]['contributions'] += data['contributions']
            totals[year]['value'] += value

            previous_value = value

    return totals


def get_yearly_with_gains(totals):
    years = []
    previous_year = None
    for year in sorted(totals):
        value = totals[year]['value']
        contrib = totals[year]['contributions']
        if previous_year:
            gain = (value - contrib / 2) / (previous_year.value + contrib / 2)
            gain_value = value - contrib - previous_year.value
        else:
            gain = 1
            gain_value = 0

        this_year = Year(year, contrib, value, gain, gain_value)
        years.append(this_year)

        previous_year = this_year

    return years


def get_history_report(matching_accounts):
    report = ''
    for account in matching_accounts:
        report += f'{get_account_history(account)}\n'

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
    else:
        return history

    year_start, year_end = util.get_start_and_end_range(years.keys())
    contributions_total = 0
    previous_shares = None
    previous_price = None
    previous_value = None
    diff_f = ''
    for year in range(year_start, year_end):
        year = str(year)
        if year in years.keys():
            contributions = years[year]['contributions']
            contributions_f = Colorable(
                'yellow',
                f'$ {contributions:,.0f}',
                '>10'
            )
            shares = years[year]['shares']
            price = years[year]['price']
        else:
            # todo: integration with ledger to get current info
            contributions = 0
            contributions_f = Colorable('red', '???', '>10')
            shares = previous_shares
            price = previous_price

        shares_f = Colorable('blue', shares, '9,.0f')
        price_f = Colorable('yellow', f'$ {price:,.2f}', '>10')

        value = shares * price
        value_f = util.get_colored_amount(value, colwidth=12, decimals=0)

        if previous_value:
            diff_f = util.get_colored_amount(
                value - previous_value,
                colwidth=13,
                decimals=0
            )

        history += (f'    {year}  {contributions_f}  {shares_f}  '
                    f'{price_f}  {value_f:>12}  {diff_f}\n')

        previous_shares = shares
        previous_price = price
        previous_value = value
        contributions_total += contributions

    if contributions_total and len(years) > 1:
        history += '          {}\n'.format(
            util.get_colored_amount(contributions_total, 10, decimals=0)
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
