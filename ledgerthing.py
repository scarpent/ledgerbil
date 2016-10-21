#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

import re

import util


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


UNSPECIFIED_PAYEE = '<Unspecified payee>'


class LedgerThing(object):

    DATE_REGEX = r'^\d{4}(?:[-/]\d\d){2}(?=(?:\s|$))'
    # date (optional number) payee  ; optional comment
    TOP_LINE_REGEX = re.compile(
        r'(' + DATE_REGEX +
        r')(?:\s+\(([^)]*)\))?\s*([^;]+)?(?:;.*$|$)'
    )
    REC_PENDING = '!'
    REC_CLEARED = '*'

    def __init__(self, lines):

        self.thing_number = 0
        self.thing_date = None
        self.payee = None
        self.transaction_code = ''  # e.g. check number
        self.lines = lines
        self.is_transaction = False

        # reconciliation
        self.rec_account = None
        self.rec_status = ''
        self.rec_amount = 0

        if self.is_transaction_start(lines[0]):
            self.is_transaction = True
            m = re.match(LedgerThing.TOP_LINE_REGEX, lines[0])

            # date can be modified
            self.thing_date = util.get_date(m.groups()[0])

            # payee and transaction code are read-only
            if m.groups()[1] is not None:
                self.transaction_code = str(m.groups()[1])
            if m.groups()[2] is None or m.groups()[2].strip() == '':
                self.payee = UNSPECIFIED_PAYEE
            else:
                self.payee = m.groups()[2].strip()

    def get_lines(self):
        if self.is_transaction:
            self.lines[0] = re.sub(
                self.DATE_REGEX,
                self.get_date_string(),
                self.lines[0]
            )
        return self.lines

    @staticmethod
    def is_new_thing(line):
        # currently, is_new_thing == is_transaction_start, but this
        # could change in future
        if LedgerThing.is_transaction_start(line):
            return True
        else:
            return False

    @staticmethod
    def is_transaction_start(line):
        match = re.match(LedgerThing.TOP_LINE_REGEX, line)
        if match:
            return util.is_valid_date(match.groups()[0])
        else:
            return False

    def get_date_string(self):
        return util.get_date_string(self.thing_date)
