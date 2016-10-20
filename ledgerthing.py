#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

import re

from datetime import date
from datetime import datetime
from dateutil.parser import parse


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LedgerThing(object):

    DATE_REGEX = r'^\d{4}([-/]\d\d){2}'
    DATE_FORMAT = '%Y/%m/%d'

    def __init__(self, lines):

        self.thing_number = 0
        self.thing_date = None
        self.lines = lines
        self.is_transaction = False

        if self.is_transaction_start(lines[0]):
            self.is_transaction = True
            date_string = re.search(
                r'(%s)' % self.DATE_REGEX,
                lines[0]
            ).group(1)
            self.thing_date = self.get_date(date_string)

    def get_lines(self):
        if self.is_transaction:
            self.lines[0] = re.sub(
                self.DATE_REGEX,
                self.get_date_string(self.thing_date),
                self.lines[0]
            )
        return self.lines

    @staticmethod
    def is_new_thing(line):
        # for now we're looking for dates as the start of transactions
        # later: payees, accounts, aliases, etc
        if LedgerThing.is_transaction_start(line):
            return True

        return False

    @staticmethod
    def is_transaction_start(line):
        # date check, pending refinement based on ledger spec
        match = re.match(
            r'({})\s+[^\s].*$'.format(LedgerThing.DATE_REGEX),
            line
        )
        if match:
            try:
                parse(match.group(1))  # verify it parses as date
                return True
            except ValueError:
                pass

        return False

    @staticmethod
    def get_date_string(the_date):
        """ @type the_date: date """
        return the_date.strftime(LedgerThing.DATE_FORMAT)

    @staticmethod
    def get_date(date_string):
        """ @type date_string: str """
        return datetime.strptime(
            date_string,
            LedgerThing.DATE_FORMAT
        ).date()
