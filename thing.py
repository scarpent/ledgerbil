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

    def __init__(self, lines):
        LedgerThing.thingCounter += 1
        self.rawlines = lines

        if self.isTransactionStart(lines[0]):
            # may not be a real date: initially for a non-transaction
            # at start of file, and later for other non-transactions elsewhere
            # todo: deal with the situation
            self.date = re.sub(r'^(\s+)', r'\1', lines[0])

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
                parse(match.group(1))
                return True
            except ValueError:
                pass

        return False
