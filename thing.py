#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re
from dateutil.parser import parse


class LedgerThing():

    dateRegex = r'\d{4}([-/]\d\d){2}'

    def __init__(self, lines, thingNumber=1, thingDate='1899/01/01'):

        self.thingNumber = thingNumber
        self.rawlines = lines

        if self.isTransactionStart(lines[0]):
            # maybe will want to use same date regex here and in isT... method
            self.date = re.search(
                r'^(%s)' % LedgerThing.dateRegex, lines[0]
            ).group(1)
        else:
            # preserve sort order by date
            self.date = thingDate

    def getLines(self):
        return self.rawlines

    @staticmethod
    def isNewThing(line):
        # for now we're looking for dates as the start of transactions
        # later: payees, accounts, aliases, etc
        if LedgerThing.isTransactionStart(line):
            return True

        return False

    @staticmethod
    def isTransactionStart(line):
        # loose date-like check, pending refinement based on ledger spec
        match = re.match(r'^(%s)\s+[^\s].*$' % LedgerThing.dateRegex, line)
        if match:
            try:
                parse(match.group(1))  # verify it parses as date
                return True
            except ValueError:
                pass

        return False
