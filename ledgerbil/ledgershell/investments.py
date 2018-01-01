import argparse
import os
import re
from collections import namedtuple

from ..colorable import Colorable
from .runner import get_ledger_command, get_ledger_output
from .settings import Settings

DOLLARS = ' -V'
SHARES = ' -X'

DOLLARS_REGEX = r'^\s*(?:(\$ -?[\d,.]+|0))(.*)$'
SHARES_REGEX = r'\s*(-?[\d,.]+) ([a-zA-Z]+)(.*)$'

Dollars = namedtuple('Dollars', 'amount account')
Shares = namedtuple('Shares', 'num symbol account')

settings = Settings()


def get_investment_command_options(
        accounts=settings.INVESTMENT_DEFAULT_ACCOUNTS,
        begin_date='',
        end_date=settings.INVESTMENT_DEFAULT_END_DATE):

    if begin_date:
        begin_date = ' --begin {}'.format(begin_date)
    end_date = '--end {}'.format(end_date)

    return '--market --price-db {prices} bal {accounts}{begin} {end}'.format(
        prices=os.path.join(settings.LEDGER_DIR, settings.PRICES_FILE),
        accounts=accounts,
        begin=begin_date,
        end=end_date
    )


def check_for_negative_dollars(amount, account):
    if amount[:3] == '$ -':
        print(
            '{warning} Negative dollar amount {amount} for "{account}." '
            'This may be a data entry mistake, or because we are '
            'looking at a date range.\n'.format(
                warning=Colorable('red', 'WARNING:'),
                amount=Colorable('red', amount),
                account=account.strip()
            )
        )


def get_lines(report_type, args):
    options = '{report} {options}'.format(
        report=report_type,
        options=get_investment_command_options(
            args.accounts,
            args.begin,
            args.end
        )
    )
    output = get_ledger_output(options)

    if args.command:
        print(get_ledger_command(options))

    return output.split('\n')


def get_dollars(args):
    """ A sample dollars report:

                  $ 1,737.19  assets
                  $ 1,387.19     401k
                    $ 798.19       big co 500 idx
                    $ 400.00       bonds idx
                    $ 189.00       cash
                    $ 150.00     ira: glass idx
                    $ 200.00     mutual: total idx
        --------------------
                  $ 1,737.19
    """
    listing = []
    lines = get_lines(DOLLARS, args)
    for line in lines:
        if line == '' or line[0] == '-':
            break
        # todo: test for 0
        #       (e.g. specifying begin and end date and things balance to 0)
        match = re.match(DOLLARS_REGEX, line)
        if match:
            dollars = Dollars(*match.groups())
            check_for_negative_dollars(dollars.amount, dollars.account)
            listing.append(dollars)
        else:
            err = "Didn't match for $ amount and name on: {}".format(line)
            raise Exception(err)

    return listing


def get_shares(args):
    """ A sample share report to help make sense of this. We will turn this
        odd lump of output into a list that matches the much nicer dollars
        report shown above.

                    $ 189.00
                 9.897 abcdx
                20.000 lmnop
                15.000 qwrty
                 5.000 yyzxx  assets
                    $ 189.00
                 9.897 abcdx
                20.000 lmnop     401k
                 9.897 abcdx       big co 500 idx
                20.000 lmnop       bonds idx
                    $ 189.00       cash
                15.000 qwrty     ira: glass idx
                 5.000 yyzxx     mutual: total idx
        --------------------
                    $ 189.00
                 9.897 abcdx
                20.000 lmnop
                15.000 qwrty
                 5.000 yyzxx
    """

    listing = []
    index = []
    lines = get_lines(SHARES, args)
    # Filter out all the extra bogus lines; after this our share list
    # will be the same length as our dollars list, with one line per
    # account "level"
    lines = [x for x in lines if re.search(r'\S  ', x)]
    # Reverse the list because we only want to use the shares for the
    # lowest matching level, so we want to encounter that first and then
    # appropriately not use later instances
    for line in reversed(lines):
        match = re.match(DOLLARS_REGEX, line)
        if match:
            # Cash lines don't have share amounts, just dollars; we'll
            # make shares/symbols be empty and just have the account
            # to keep our lists lined up
            dollars = Dollars(*match.groups())
            check_for_negative_dollars(dollars.amount, dollars.account)
            listing.append(Shares('', '', dollars.account))
        else:
            # Only use the shares from the last/lowest instance, e.g.
            # we want "5.000 yyzxx" to match up with "mutual: total idx";
            # if we've already found that shares/symbol combo, e.g.
            # when we again see "5.000 yyzxx" with assets, we'll again
            # make shares/symbols be empty and keep the account to line
            # things up. NOTE THAT WE'RE MAKING A BIG ASSUMPTION that
            # the shares/symbol combo will be unique across accounts.
            match = re.match(SHARES_REGEX, line)
            shares = Shares(*match.groups())
            if (shares.num, shares.symbol) in index:
                shares = Shares('', '', shares.account)
            else:
                index.append((shares.num, shares.symbol))
            listing.append(shares)

    listing.reverse()  # Reverse back to match dollars list order
    return listing


def get_investment_report(args):
    """ We want to put the separate shares and dollars reports
        together to get something like this:

                           $ 1,737.19   assets
                           $ 1,387.19      401k
         9.897 abcdx         $ 798.19        big co 500 idx
        20.000 lmnop         $ 400.00        bonds idx
                             $ 189.00        cash
        15.000 qwrty         $ 150.00      ira: glass idx
         5.000 yyzxx         $ 200.00      mutual: total idx
    """

    share_listing = get_shares(args)
    dollar_listing = get_dollars(args)

    report = ''

    for shares, dollars in zip(share_listing, dollar_listing):

        assert shares.account == dollars.account, \
            'shares: {}, dollars: {}'.format(
                shares.account,
                dollars.account
            )

        dollar_color = 'red' if '-' in dollars.amount else 'green'

        report += ('{shares} {symbol} {dollars} {investment}\n'.format(
            shares=Colorable(
                'gray',
                shares.num,
                column_width=12,
                right_adjust=True,
                bright=True
            ),
            symbol=Colorable(
                'purple',
                shares.symbol,
                column_width=5
            ),
            dollars=Colorable(
                dollar_color,
                dollars.amount,
                column_width=16,
                right_adjust=True
            ),
            investment=Colorable('blue', dollars.account)
        ))

    return report


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
            default=settings.INVESTMENT_DEFAULT_ACCOUNTS,
            help='balances for specified accounts, default = {}'.format(
                settings.INVESTMENT_DEFAULT_ACCOUNTS
            )
        )
        parser.add_argument(
            '-b', '--begin',
            type=str,
            metavar='DATE',
            default='',
            help='begin date'
        )
        parser.add_argument(
            '-e', '--end',
            type=str,
            metavar='DATE',
            default=settings.INVESTMENT_DEFAULT_END_DATE,
            help='end date, default = {}'.format(
                settings.INVESTMENT_DEFAULT_END_DATE
            )
        )
        parser.add_argument(
            '-c', '--command',
            action='store_true',
            help='print ledger commands used'
        )

        return parser.parse_args(args)


def main(argv):
    args = ArgHandler.get_args(argv)
    print(get_investment_report(args))
