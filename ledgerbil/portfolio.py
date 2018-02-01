import argparse
import json
import re
from collections import defaultdict, namedtuple

from . import util
from .colorable import Colorable
from .ledgerbilexceptions import LdgPortfolioError
from .settings import Settings

settings = Settings()

Year = namedtuple('Year', 'year contributions transfers value gain gain_value')


def strip_assets_prefix(s):
    return re.sub('(?i)assets: ?', '', s)


def get_portfolio_report(args):
    matched, included_years = get_matching_accounts(args.accounts_regex)

    if not matched:
        return 'No accounts matched {}'.format(args.accounts_regex)

    if args.history:
        report = get_history_report(matched)
    elif args.list:
        report = strip_assets_prefix(
            '\n'.join(sorted([m['account'] for m in matched]))
        )
        count = f"\n{len(matched)} account{'' if len(matched) == 1 else 's'}"
        report += str(Colorable('cyan', count))
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

    return sorted(matched, key=lambda k: k['account']), included_years


def validate_json_year_keys(year):
    valid_keys = {'symbol', 'price', 'shares',
                  'contributions', 'transfers', 'note'}
    if not all([k in valid_keys for k in year.keys()]):
        raise LdgPortfolioError(f'Invalid key in {year.keys()}')


def get_performance_report(accounts, included_years):
    year_start, year_end = util.get_start_and_end_range(included_years)
    totals = get_yearly_combined_accounts(accounts, year_start, year_end)
    years = get_yearly_with_gains(totals)
    info = f"{len(years)} year{'' if len(years) == 1 else 's'}, "
    info += f"{len(accounts)} account{'' if len(accounts) == 1 else 's'}: "
    info += ', '.join([account['account'] for account in accounts[:2]])
    if len(accounts) > 2:
        info += ', ...'
    return '{info}\n\n{report}'.format(
        info=strip_assets_prefix(info),
        report=get_performance_report_years(years)
    )


COL_GAIN = 7
COL_CONTRIB = 9
COL_TRANSFERS = 10
COL_VALUE = 11
COL_GAIN_VALUE = 11


def get_annualized_total_return(gains, num_years):
    return (pow(util.product(gains[-num_years:]), 1 / num_years) - 1) * 100


def get_gain(gains, num_years, total_years):
    if len(gains) >= num_years:
        return util.get_colored_amount(
            get_annualized_total_return(gains, num_years),
            colwidth=COL_GAIN,
            prefix='',
            positive='white'
        )
    elif total_years < num_years:
        return ''
    else:
        return ' ' * COL_GAIN


def get_performance_report_years(years):
    total_years = len(years)

    header3 = '' if total_years < 3 else f"{'3 yr %':>{COL_GAIN}}"
    header5 = '' if total_years < 5 else f"{'5 yr %':>{COL_GAIN}}"
    header10 = '' if total_years < 10 else f"{'10 yr %':>{COL_GAIN}}"

    report = str(Colorable(
        'cyan',
        (f"year  {'contrib':>{COL_CONTRIB}}  {'transfers':>{COL_TRANSFERS}}  "
         f"{'value':>{COL_VALUE}}  {'gain %':>{COL_GAIN}}  "
         f"{'gain val':>{COL_GAIN_VALUE}}  {'all %':>{COL_GAIN}}  "
         f'{header3}  {header5}  {header10}\n')
    ))

    contrib_total = 0
    transfers_total = 0
    gain_val_total = 0
    gains = []
    for year in years:
        gains.append(year.gain)
        if year.contributions:
            contrib = Colorable(
                'yellow',
                util.get_plain_amount(year.contributions, COL_CONTRIB, 0)
            )
        else:
            contrib = ' ' * COL_CONTRIB
        # todo: tests for these rounding things...
        if year.transfers and (f'{year.transfers:.0f}' not in ('0', '-0')):
            transfers = util.get_colored_amount(year.transfers,
                                                colwidth=COL_TRANSFERS,
                                                decimals=0)
        else:
            transfers = ' ' * COL_TRANSFERS
        value = util.get_plain_amount(year.value, COL_VALUE, 0)
        if year.gain == 1:
            gain = ' ' * COL_GAIN
            gain_value = ' ' * COL_GAIN_VALUE
        else:
            gain = get_gain([year.gain], 1, 1)
            gain_value = util.get_colored_amount(year.gain_value,
                                                 colwidth=COL_GAIN_VALUE,
                                                 decimals=0)

        gain_all = get_gain(gains, len(gains), total_years)
        gain_3 = get_gain(gains, 3, total_years)
        gain_5 = get_gain(gains, 5, total_years)
        gain_10 = get_gain(gains, 10, total_years)

        report += (f'{year.year}  {contrib}  {transfers}  {value}  '
                   f'{gain}  {gain_value}  {gain_all}  '
                   f'{gain_3}  {gain_5}  {gain_10}\n')

        contrib_total += year.contributions
        transfers_total += year.transfers
        gain_val_total += year.gain_value

    if len(years) > 1:
        if contrib_total:
            contrib_total_f = util.get_colored_amount(contrib_total,
                                                      colwidth=COL_CONTRIB,
                                                      decimals=0)
        else:
            contrib_total_f = ' ' * COL_CONTRIB
        if transfers_total:
            transfers_total_f = util.get_colored_amount(transfers_total,
                                                        colwidth=COL_TRANSFERS,
                                                        decimals=0)
        else:
            transfers_total_f = ' ' * COL_TRANSFERS
        gain_val_total_f = util.get_colored_amount(gain_val_total,
                                                   colwidth=COL_GAIN_VALUE,
                                                   decimals=0)
        report += (f'      {contrib_total_f}  {transfers_total_f}  '
                   f'{"":{COL_VALUE + COL_GAIN + 2}}  {gain_val_total_f}')

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
                    totals[year]['transfers'] += 0
                    totals[year]['value'] += previous_value
                continue

            data = account['years'][str(year)]
            validate_json_year_keys(data)

            value = data['price'] * data['shares']
            totals[year]['contributions'] += data['contributions']
            totals[year]['transfers'] += data.get('transfers', 0)
            totals[year]['value'] += value
            previous_value = value

    return totals


def get_yearly_with_gains(totals):
    years = []
    previous_year = None
    for year in sorted(totals):
        value = totals[year]['value']
        contrib = totals[year]['contributions']
        transfers = totals[year]['transfers']

        previous_value = previous_year.value if previous_year else 0
        gain = ((value - (contrib + transfers) / 2)
                / (previous_value + (contrib + transfers) / 2))
        gain_value = value - contrib - transfers - (previous_value or 0)

        this_year = Year(year, contrib, transfers, value, gain, gain_value)
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
        account=Colorable('purple', strip_assets_prefix(account['account'])),
        label=Colorable('white', labels, '>79') if account['labels'] else ''
    )

    years = account['years']
    if len(years):
        percent = '%' if len(years) > 1 else ''
        header = (
            f"\n    year  {'contrib':>10}  {'transfers':>10}  {'shares':>9}  "
            f"{'price':>10}  {'value':>12}  {percent:>8}\n"
        )
        history += f"{Colorable('cyan', header)}"
    else:
        return history

    year_start, year_end = util.get_start_and_end_range(years.keys())
    contrib_total = 0
    transfers_total = 0
    previous_shares = None
    previous_price = None
    previous_value = 0
    for year in range(year_start, year_end):
        year = str(year)
        transfers_f = ' ' * 10
        contrib_f = ' ' * 10
        if year in years.keys():
            validate_json_year_keys(years[year])
            contrib = years[year]['contributions']
            if contrib:
                contrib_f = Colorable('yellow', f'$ {contrib:,.0f}', '>10')
            transfers = years[year].get('transfers', 0)
            if transfers:
                transfers_f = util.get_colored_amount(transfers, 10, 0)
            shares = years[year]['shares']
            price = years[year]['price']
        else:
            # todo: integration with ledger to get current info
            contrib = 0
            contrib_f = Colorable('red', '???', '>10')
            shares = previous_shares
            price = previous_price

        shares_f = Colorable('blue', shares, '9,.0f')
        price_f = Colorable('yellow', f'$ {price:,.2f}', '>10')

        value = shares * price
        value_f = util.get_plain_amount(value, colwidth=12, decimals=0)

        gain_f = ' ' * 8
        gain = ((value - (contrib + transfers) / 2)
                / (previous_value + (contrib + transfers) / 2) - 1) * 100
        if gain != 0:
            gain_f = util.get_colored_amount(gain,
                                             colwidth=8,
                                             prefix='',
                                             positive='white')

        history += (
            f'    {year}  {contrib_f}  {transfers_f}  {shares_f}  '
            f'{price_f}  {value_f}  {gain_f}\n'
        )

        previous_shares = shares
        previous_price = price
        previous_value = value
        contrib_total += contrib
        transfers_total += transfers

    if len(years) > 1:
        contrib_total_f = util.get_colored_amount(contrib_total, 10, 0)
        if transfers_total:
            transfers_total_f = util.get_colored_amount(transfers_total, 10, 0)
        else:
            transfers_total_f = ' ' * 10
        history += f'          {contrib_total_f}  {transfers_total_f}\n'

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
        metavar='REGEX',
        dest='accounts_regex',
        default='.*',
        help='include accounts that match this regex, default = .* (all)'
    )
    parser.add_argument(
        '-H', '--history',
        action='store_true',
        help='show account history'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='list account names'
    )

    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    print(get_portfolio_report(args))
