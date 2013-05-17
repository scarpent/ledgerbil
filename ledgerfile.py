#!/usr/bin/python

"""ledger files: journal, schedule file, or preview file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LedgerFile():

    def __init__(self):
        self.thingCounter = 0
        self.currentDate = '1899/01/01'
