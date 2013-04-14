#!/usr/bin/python

"""unit test for thing.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from thing import LedgerThing


class GetLines(unittest.TestCase):

    def testGetLines(self):
        lines = ['abc\n', 'xyz\n']
        thing = LedgerThing(lines)
        self.assertEqual(lines, thing.getLines())

class IsNewThing(unittest.TestCase):

    def testValidTransactionStart(self):
        """date should be recognized as the start of a transaction (return true)"""
        line = '2013/04/14 abc store'
        self.assertTrue(LedgerThing.isNewThing(line))

    def testValidTransactionStartWithTabs(self):
        """date should be recognized as the start of a transaction (return true)"""
        line = '2013/04/14\t\tabc store'
        self.assertTrue(LedgerThing.isNewThing(line))

    def testLeadingWhiteSpace(self):
        """leading whitespace should return false"""
        line = '    2013/04/14 abc store'
        self.assertFalse(LedgerThing.isNewThing(line))

    def testDateOnly(self):
        """date only should return false"""
        line = '2013/04/14 '
        self.assertFalse(LedgerThing.isNewThing(line))

    def testEmptyLine(self):
        """empty line should return false"""
        line = ''
        self.assertFalse(LedgerThing.isNewThing(line))

    def testNewline(self):
        """newline should return false"""
        line = '\n'
        self.assertFalse(LedgerThing.isNewThing(line))

    def testWhitespace(self):
        """whitespace should return false"""
        line = '            \t    '
        self.assertFalse(LedgerThing.isNewThing(line))

    def testInvalidDate(self):
        """invalid date format should return false"""
        line = '//201304/14 abc store'
        self.assertFalse(LedgerThing.isNewThing(line))

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
