#!/usr/bin/python

"""supports thing testing with common setUp"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from thing import LedgerThing

class ThingTester(unittest.TestCase):

    START_DATE = '1899/01/01'

    def setUp(self):
        LedgerThing.thingCounter = 0
        LedgerThing.date = ThingTester.START_DATE
