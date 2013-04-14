#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Thing():

    _rawlines = []
    _date = ''

    def __init__(self, lines):
        self._rawlines = lines

    def getLines(self):
        return self._rawlines