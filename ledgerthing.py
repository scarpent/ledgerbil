#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re
from dateutil.parser import parse
from datetime import date
from datetime import datetime


class LedgerThing(object):

    DATE_REGEX = r'^\d{4}([-/]\d\d){2}'
    DATE_FORMAT = '%Y/%m/%d'

    def __init__(self, lines):

        self.thingNumber = 0  # to be overridden by file's addThing method
        self.thingDate = None
        self.lines = lines
        self.isTransaction = False

        if self.isTransactionStart(lines[0]):
            self.isTransaction = True
            dateString = re.search(
                r'(%s)' % self.DATE_REGEX,
                lines[0]
            ).group(1)
            self.thingDate = self.getDate(dateString)

    def getLines(self):
        if self.isTransaction:
            self.lines[0] = re.sub(
                self.DATE_REGEX,
                self.getDateString(self.thingDate),
                self.lines[0]
            )
        return self.lines

    @staticmethod
    def isNewThing(line):
        # for now we're looking for dates as the start of transactions
        # later: payees, accounts, aliases, etc
        if LedgerThing.isTransactionStart(line):
            return True

        return False

    @staticmethod
    def isTransactionStart(line):
        # date check, pending refinement based on ledger spec
        match = re.match(r'(%s)\s+[^\s].*$' % LedgerThing.DATE_REGEX, line)
        if match:
            try:
                parse(match.group(1))  # verify it parses as date
                return True
            except ValueError:
                pass

        return False

    @staticmethod
    def getDateString(date):
        """ @type date: date """
        return date.strftime(LedgerThing.DATE_FORMAT)


    @staticmethod
    def getDate(dateString):
        """ @type dateString: str """
        return datetime.strptime(dateString, LedgerThing.DATE_FORMAT).date()
