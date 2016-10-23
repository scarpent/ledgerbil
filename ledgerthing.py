#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

import re

import util

from ledgerbilexceptions import LdgReconcilerMoreThanOneMatchingAccount


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


UNSPECIFIED_PAYEE = '<Unspecified payee>'

REC_STATUS_ERROR_MESSAGE = (
    "I don't know how to handle different reconciliation statuses "
    "(pending/cleared) for the same account within a transaction "
    " (will use the first one found: '{status}'). Date: {date}, "
    "Payee: {payee}"
)


class LedgerThing(object):

    DATE_REGEX = r'^\d{4}(?:[-/]\d\d){2}(?=(?:\s|$))'
    # date (optional number) payee  ; optional comment
    TOP_LINE_REGEX = re.compile(
        r'(' + DATE_REGEX +
        r')(?:\s+\(([^)]*)\))?\s*([^;]+)?(?:;.*$|$)'
    )
    REC_PENDING = '!'
    REC_CLEARED = '*'

    def __init__(self, lines, reconcile_account=None):

        self.thing_number = 0
        self.thing_date = None
        self.payee = None
        self.transaction_code = ''  # e.g. check number
        self.lines = lines
        self.is_transaction = False

        # reconciliation
        self.rec_account = reconcile_account  # could be partial
        self.rec_account_matches = []  # there should be only one match
        self.rec_status = ''
        self.rec_amount = 0

        if self.is_transaction_start(lines[0]):
            self.is_transaction = True
            self._parse_top_line(lines[0])

        if self.is_transaction and self.rec_account:
            self._parse_transaction_lines(lines[1:])

    def _parse_top_line(self, line):
        m = re.match(LedgerThing.TOP_LINE_REGEX, line)

        the_date, code, payee = m.groups()

        # date can be modified
        self.thing_date = util.get_date(the_date)

        # payee and transaction code are read-only
        if code is not None:
            self.transaction_code = str(code)
        if payee is None or payee.strip() == '':
            self.payee = UNSPECIFIED_PAYEE
        else:
            self.payee = payee.strip()

    def _parse_transaction_lines(self, lines):
        if not self.rec_account or not lines:
            # currently only care about transaction lines if reconciling
            return

        entry_regex = re.compile(
            r'^\s+'                      # opening indent
            r'([!*])?'                   # optional pending/cleared
            r'(?:\s*)?'                  # optional whitespace after p/c
            r'([^;]*?)'                  # account
            r'\(?([-+*/()$\d.\s]+)?\)?'  # optional amount expression
            r'(?:\s\s;.*$|$)'            # optional end comment
        )

        # - most likely only one line for the account we're reconciling,
        #   but we'll have to handle more than one
        # - we only care about total for the account we're reconciling,
        #   but we need to total everything up in case our account
        #   doesn't have a dollar amount and we need to calculate it

        transaction_total = 0
        account_total = 0
        need_math = False
        previous_status = None
        for line in lines:
            if re.match(r'^(\s*;|$|[#%|*])', line):
                continue  # ignore comments and empty lines

            m = re.match(entry_regex, line)
            if not m:
                continue

            status, account, amount = m.groups()

            if amount is not None:
                amount = amount.strip()
                if amount == '':
                    amount = None
                else:
                    amount = util.eval_expr(
                        re.sub(r'\$', '', amount)
                    )
                    transaction_total += amount

            if self.rec_account in account:
                if account.strip() not in self.rec_account_matches:
                    self.rec_account_matches.append(account.strip())

                if previous_status is None:
                    self.rec_status = status if status else ''
                    previous_status = self.rec_status
                else:
                    if previous_status != status \
                            and previous_status != 'foobar' \
                            and len(self.rec_account_matches) < 2:

                        # not going to bother showing this if multiple
                        # account matches since it's blowing up anyway
                        # and probably because of the multiple matches
                        previous_status = 'foobar'
                        print(REC_STATUS_ERROR_MESSAGE.format(
                                status=self.rec_status,
                                date=self.get_date_string(),
                                payee=self.payee
                            )
                        )

                if amount is None:
                    need_math = True
                else:
                    account_total += amount

        if len(self.rec_account_matches) > 1:
            raise LdgReconcilerMoreThanOneMatchingAccount(
                self.rec_account_matches
            )

        if len(self.rec_account_matches) > 0:
            if need_math:
                # transaction_total should be 0; use it to adjust
                account_total -= transaction_total
                transaction_total -= transaction_total
                assert transaction_total == 0
            self.rec_amount = account_total

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
