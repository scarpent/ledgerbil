#!/usr/bin/python

"""unit test for thing.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from thing import LedgerThing


class Constructor(unittest.TestCase):

    def testInitialNonTransactionDate(self):
        """when 1st thing in file is a non-transaction, it has default date"""
        thing = LedgerThing(['blah', 'blah blah blah'])
        # todo: check for none (also, not initial?)
        self.assertEqual(ThingTester.START_DATE, thing.date)

    def testLaterNonTransactionDate(self):
        """later non-transaction things inherit date of preceding thing"""
        thingOne = LedgerThing(['2013/04/16 blah', '    ; something...'])
        thingTwo = LedgerThing(['blah', 'blah blah blah'])
        self.assertEqual(thingOne.date, thingTwo.date)


class GetLines(unittest.TestCase):

    def testGetLines(self):
        """lines can be entered and retrieved as is"""
        lines = ['abc\n', 'xyz\n']
        thing = LedgerThing(lines)
        self.assertEqual(lines, thing.getLines())


class isNewThing(unittest.TestCase):

    def testIsNewThing(self):
        """should be recognized as a new ledger 'thing' """
        line = '2013/04/15 abc store'
        self.assertTrue(LedgerThing.isNewThing(line))

    def testIsNotThing(self):
        """should not be a new thing"""
        line = ''
        self.assertFalse(LedgerThing.isNewThing(line))


class isTransactionStart(unittest.TestCase):

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
