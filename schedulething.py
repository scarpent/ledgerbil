#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'



from ledgerthing import LedgerThing


class ScheduleThing(LedgerThing):

    def __init__(self, lines):
        super(ScheduleThing, self).__init__(lines)

