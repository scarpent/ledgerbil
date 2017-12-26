#!/usr/bin/env python3
import argparse
import os
import re
import sys

from ledger_util import get_ledger_output
from settings import Settings

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
            'WARNING: Negative dollar amount {amount} for {name}. '
            'This may be a data entry mistake, or because we are '
            'looking at a date range.'.format(
                amount=amount,
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
            match = re.match(r'\s*([\d,.]+ [a-zA-Z]+)(.*)$', line)
            shares, name = match.groups()
            if shares in index:
                shares = ''
            else:
                index.append(shares)
            listing.append((shares, name))

    listing.reverse()
    return listing


def run(args):

    share_listing = get_shares(args)
    dollar_listing = get_dollars(args)

    for share, dollar in zip(share_listing, dollar_listing):

        assert share[1] == dollar[1], 'share: {}, dollar: {}'.format(
            share[1],
            dollar[1]
        )

        print('{shares:>18} {dollars:>16} {investment}'.format(
            shares=share[0],
            dollars=dollar[0],
            investment=dollar[1]
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

        # todo: specify default
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
        # todo: specify default (tomorrow)
        parser.add_argument(
            '-e', '--end',
            type=str,
            default=s.INVESTMENT_DEFAULT_END_DATE,
            help='end date'
        )

        return parser.parse_args(args)


def main(argv=None):  # pragma: no cover

    if argv is None:
        argv = sys.argv[1:]

    args = ArgHandler.get_args(argv)

    run(args)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
