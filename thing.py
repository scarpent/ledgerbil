#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re
from dateutil.parser import parse


class LedgerThing():

    thingCounter = 0
    date = '1899/01/01'

    def __init__(self, lines):
        LedgerThing.thingCounter += 1

        self.thingNumber = LedgerThing.thingCounter
        self.rawlines = lines

        if self.isTransactionStart(lines[0]):
            # maybe will want to use same date regex here and in isT... method
            self.date = re.search(r'^(\S+)', lines[0]).group(1)
            LedgerThing.date = self.date
        else:
            # preserve sort order by date
            self.date = LedgerThing.date

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
        match = re.match(r'^([-0-9/]{6,})\s+[^\s].*$', line)
        if match:
            try:
                parse(match.group(1))  # verify it parses as date
                return True
            except ValueError:
                pass

        return False
