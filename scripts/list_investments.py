#!/usr/bin/env python

""" A better listing of investment share and dollar totals """

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re
import sys

from ledger_util import get_ledger_output
from settings import INVESTMENT_COMMAND_OPTIONS

DOLLARS = ' -V'
SHARES = ' -X'


def check_for_negative_dollars(amount, name):
    if amount[:3] == '$ -':
        # todo: or looking at a slice of dates...
        print(
            'WARNING: Negative dollar amount {amount} for {name}. '
            'This is likely caused by a data entry mistake.'.format(
                amount=amount,
                name=name.strip()
            )
        )


def get_dollars():
    listing = []
    lines = get_ledger_output(
        '{} {}'.format(DOLLARS, INVESTMENT_COMMAND_OPTIONS)
    ).split('\n')
    for line in lines:
        if line[0] == '-':
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


def get_shares():
    listing = []
    index = []
    lines = get_ledger_output(
        '{} {}'.format(SHARES, INVESTMENT_COMMAND_OPTIONS)
    ).split('\n')
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


def run():

    share_listing = get_shares()
    dollar_listing = get_dollars()

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


def main(argv=None):  # pragma: no cover

    if argv is None:
        argv = sys.argv[1:]

    run()


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
