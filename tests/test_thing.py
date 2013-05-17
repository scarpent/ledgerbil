#!/usr/bin/python

"""unit test for thing.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from thing import LedgerThing
from redirector import ThingTester


class Constructor(ThingTester):

    def testKnowsHowToCountTransactions(self):
        """should count two actual transactions"""
        LedgerThing(['2013/04/15 blah', '    ; something...'])
        LedgerThing(['2013/04/15 more blah', '    ; something...'])
        self.assertEquals(2, LedgerThing.thingCounter)

    def testKnowsHowToCountNonTransactions(self):
        """should count three non-transactions"""
        # todo: add here if/when a way to tell if a transaction
        LedgerThing(['blah', 'blah blah blah'])
        LedgerThing(['mountain', 'dew'])
        LedgerThing(['qwerty'])
        self.assertEquals(3, LedgerThing.thingCounter)

    def testInitialNonTransactionDate(self):
        """when 1st thing in file is a non-transaction, it has default date"""
        thing = LedgerThing(['blah', 'blah blah blah'])
        self.assertEqual(ThingTester.START_DATE, thing.date)

    def testLaterNonTransactionDate(self):
        """later non-transaction things inherit date of preceding thing"""
        thingOne = LedgerThing(['2013/04/16 blah', '    ; something...'])
        thingTwo = LedgerThing(['blah', 'blah blah blah'])
        self.assertEqual(thingOne.date, thingTwo.date)


class GetLines(ThingTester):

    def testGetLines(self):
        """lines can be entered and retrieved as is"""
        lines = ['abc\n', 'xyz\n']
        thing = LedgerThing(lines)
        self.assertEqual(lines, thing.getLines())


class isNewThing(ThingTester):

    def testIsNewThing(self):
        """should be recognized as a new ledger 'thing' """
        line = '2013/04/15 abc store'
        self.assertTrue(LedgerThing.isNewThing(line))

    def testIsNotThing(self):
        """should not be a new thing"""
        line = ''
        self.assertFalse(LedgerThing.isNewThing(line))


class isTransactionStart(ThingTester):

    def testValidTransactionStart(self):
        """date recognized as the start of a transaction (return true)"""
        line = '2013/04/14 abc store'
        self.assertTrue(LedgerThing.isTransactionStart(line))

    def testValidTransactionStartWithTabs(self):
        """date recognized as the start of a transaction (return true)"""
        line = '2013/04/14\t\tabc store'
        self.assertTrue(LedgerThing.isTransactionStart(line))

    def testLeadingWhiteSpace(self):
        """leading whitespace should return false"""
        line = '    2013/04/14 abc store'
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testDateOnly(self):
        """date only should return false"""
        line = '2013/04/14 '
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testEmptyLine(self):
        """empty line should return false"""
        line = ''
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testNewline(self):
        """newline should return false"""
        line = '\n'
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testWhitespace(self):
        """whitespace should return false"""
        line = '            \t    '
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testInvalidDate(self):
        """invalid date should return false"""
        line = '2013/02/30 abc store'
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testInvalidDateFormatMonth(self):
        """valid date but invalid (for ledger) date fmt should return false"""
        line = '2013/5/12 abc store'
        self.assertFalse(LedgerThing.isTransactionStart(line))

    def testInvalidDateFormatDay(self):
        """valid date but invalid (for ledger) date fmt should return false"""
        line = '2013/06/1 abc store'
        self.assertFalse(LedgerThing.isTransactionStart(line))

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
