#!/usr/bin/python

"""unit test for thing.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from thing import LedgerThing


class Constructor(unittest.TestCase):

    def testKnowsHowToCountTransactions(self):
        LedgerThing.thingCounter = 0
        LedgerThing(['2013/04/15 blah', '    ; something...'])
        LedgerThing(['2013/04/15 more blah', '    ; something...'])
        self.assertEquals(LedgerThing.thingCounter, 2)

    def testKnowsHowToCountNonTransactions(self):
        LedgerThing.thingCounter = 0
        LedgerThing(['blah', 'blah blah blah'])
        LedgerThing(['mountain', 'dew'])
        LedgerThing(['qwerty'])
        self.assertEquals(LedgerThing.thingCounter, 3)


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
        """invalid date format should return false"""
        line = '//201304/14 abc store'
        self.assertFalse(LedgerThing.isTransactionStart(line))

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
