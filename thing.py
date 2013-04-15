#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re
from dateutil.parser import parse


class LedgerThing():

    def __init__(self, lines):
        self.rawlines = lines

    def getLines(self):
        return self.rawlines

    @staticmethod
    def isNewThing(line):
        # for now we're looking for dates as the start of transactions
        # later: payees, accounts, aliases, etc
        match = re.match(r'^([-0-9/]{6,})[\s]+[^\s].*$', line)
        if match:
            try:
                parse(match.group(1))
                return True
            except ValueError:
                pass

        return False
