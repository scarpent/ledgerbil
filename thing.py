#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re
from dateutil.parser import parse


class LedgerThing():

    rawlines = []
    date_ = ''

    def __init__(self, lines):
        self.rawlines = lines

    def getLines(self):
        return self.rawlines

    @staticmethod
    def isTransactionStart(line):
        # a date at the start of a line with something following it
        # makes it a transaction
        match = re.match(r'^([-0-9/]{6,})[\s]+[^\s].*$', line)
        if match:
            try:
                parse(match.group(1))
                return True
            except ValueError:
                pass

        return False
