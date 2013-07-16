#!/usr/bin/python

"""unit test for ledgerthing.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from unittest import TestCase

from datetime import date

from ledgerthing import LedgerThing


class Constructor(TestCase):

    def testNonTransactionDate(self):
        """non-transactions initially have date = None"""
        thing = LedgerThing(['blah', 'blah blah blah'])
        self.assertIsNone(thing.thingDate)

    def testTransactionDate(self):
        """later non-transaction things inherit date of preceding thing"""
        thing = LedgerThing(['2013/05/18 blah', '    ; something...'])
        self.assertEqual(thing.thingDate, date(2013, 5, 18))


class GetLines(TestCase):

    def testGetLines(self):
        """lines can be entered and retrieved as is"""
        lines = ['abc\n', 'xyz\n']
        thing = LedgerThing(lines)
        self.assertEqual(lines, thing.getLines())


class isNewThing(TestCase):

    def testIsNewThing(self):
        """should be recognized as a new ledger 'thing' """
        line = '2013/04/15 abc store'
        self.assertTrue(LedgerThing.isNewThing(line))

    def testIsNotThing(self):
        """should not be a new thing"""
        line = ''
        self.assertFalse(LedgerThing.isNewThing(line))


class isTransactionStart(TestCase):

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
