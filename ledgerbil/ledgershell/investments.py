import argparse
import os
import re

from ..colorable import Colorable
from .runner import get_ledger_output
from .settings import Settings

DOLLARS = ' -V'
SHARES = ' -X'

s = Settings()


def get_investment_command_options(accounts=s.INVESTMENT_DEFAULT_ACCOUNTS,
                                   begin_date='',
                                   end_date=s.INVESTMENT_DEFAULT_END_DATE):
    if begin_date:
        begin_date = '--begin {}'.format(begin_date)
    end_date = '--end {}'.format(end_date)

    return '--market --price-db {prices} bal {accounts} {begin} {end}'.format(
        prices=os.path.join(s.LEDGER_DIR, s.PRICES_FILE),
        accounts=accounts,
        begin=begin_date,
        end=end_date
    )


def check_for_negative_dollars(amount, name):
    if amount[:3] == '$ -':
        print(
            '{warning} Negative dollar amount {amount} for "{name}." '
            'This may be a data entry mistake, or because we are '
            'looking at a date range.\n'.format(
                warning=Colorable('red', 'WARNING:'),
                amount=Colorable('red', amount),
                name=name.strip()
            )
        )


def get_lines(report_type, args):
    return get_ledger_output('{report} {options}'.format(
        report=report_type,
        options=get_investment_command_options(
            args.accounts,
            args.begin,
            args.end
        )
    )).split('\n')


def get_dollars(args):
    listing = []
    lines = get_lines(DOLLARS, args)
    for line in lines:
        if line == '' or line[0] == '-':
            break
        # todo: test for 0
        #       (e.g. specifying begin and end date and things balance to 0)
        match = re.match(r'^\s*(?:(\$ -?[\d,.]+|0))(.*)$', line)
        if match:
            amount, name = match.groups()
            check_for_negative_dollars(amount, name)
            listing.append((amount, name))
        else:
            err = "Didn't match for $ amount and name on: {}".format(line)
            raise Exception(err)

    return listing


def get_shares(args):
    listing = []
    index = []
    lines = get_lines(SHARES, args)
    # Filter out all the extra bogus lines
    lines = [x for x in lines if re.search(r'\S  ', x)]
    for line in reversed(lines):
        match = re.match(r'\s*(\$ -?[\d,.]+)(.*)$', line)
        if match:
            # Cash lines don't have share amounts, just dollars
            amount, name = match.groups()
            check_for_negative_dollars(amount, name)
            listing.append(('', name))
        else:
            # Only use the shares from the last instance
            match = re.match(r'\s*-?([\d,.]+ [a-zA-Z]+)(.*)$', line)
            shares, name = match.groups()
            if shares in index:
                shares = ''
            else:
                index.append(shares)
            listing.append((shares, name))

    listing.reverse()
    return listing


def share_split(shares):
    match = re.match(r'^(.*\S\s)(.*)$', shares)
    if match:
        return match.groups()
    else:
        return shares, ''


def run(args):

    share_listing = get_shares(args)
    dollar_listing = get_dollars(args)

    for share, dollar in zip(share_listing, dollar_listing):

        assert share[1] == dollar[1], 'share: {}, dollar: {}'.format(
            share[1],
            dollar[1]
        )

        shares, symbol = share_split(share[0])

        dollar_color = 'red' if '-' in dollar[0] else 'green'

        print('{shares}{symbol} {dollars} {investment}'.format(
            shares=Colorable(
                'gray',
                shares,
                column_width=13,
                right_adjust=True,
                bright=True
            ),
            symbol=Colorable(
                'purple',
                symbol,
                column_width=5
            ),
            dollars=Colorable(
                dollar_color,
                dollar[0],
                column_width=16,
                right_adjust=True
            ),
            investment=Colorable('blue', dollar[1])
        ))


class ArgHandler(object):

    @staticmethod
    def get_args(args):
        parser = argparse.ArgumentParser(
            prog='list_investments.py',
            formatter_class=(
                lambda prog: argparse.HelpFormatter(
                    prog,
                    max_help_position=36
                )
            )
        )
        parser.add_argument(
            '-a', '--accounts',
            type=str,
            default=s.INVESTMENT_DEFAULT_ACCOUNTS,
            help='balances for accounts'
        )
        parser.add_argument(
            '-b', '--begin',
            type=str,
            default='',
            help='begin date'
        )
        parser.add_argument(
            '-e', '--end',
            type=str,
            default=s.INVESTMENT_DEFAULT_END_DATE,
            help='end date'
        )

        return parser.parse_args(args)


def main(argv):
    args = ArgHandler.get_args(argv)
    run(args)
