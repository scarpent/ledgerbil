#!/usr/bin/python

"""unit test for ledgerthing.py"""

from unittest import TestCase

from datetime import date

from ledgerthing import LedgerThing


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Constructor(TestCase):

    def test_non_transaction_date(self):
        """non-transactions initially have date = None"""
        thing = LedgerThing(['blah', 'blah blah blah'])
        self.assertIsNone(thing.thingDate)

    def test_transaction_date(self):
        """later non-transaction things inherit preceding thing date"""
        thing = LedgerThing(['2013/05/18 blah', '    ; something...'])
        self.assertEqual(thing.thingDate, date(2013, 5, 18))


class GetLines(TestCase):

    def test_get_lines(self):
        """lines can be entered and retrieved as is"""
        lines = ['abc\n', 'xyz\n']
        thing = LedgerThing(lines)
        self.assertEqual(lines, thing.get_lines())


class IsNewThing(TestCase):

    def test_is_new_thing(self):
        """should be recognized as a new ledger 'thing' """
        line = '2013/04/15 abc store'
        self.assertTrue(LedgerThing.is_new_thing(line))

    def test_is_not_thing(self):
        """should not be a new thing"""
        line = ''
        self.assertFalse(LedgerThing.is_new_thing(line))


class IsTransactionStart(TestCase):

    def test_valid_transaction_start(self):
        """date recognized as the start of a transaction"""
        line = '2013/04/14 abc store'
        self.assertTrue(LedgerThing.is_transaction_start(line))

    def test_valid_transaction_start_with_tabs(self):
        """date recognized as the start of a transaction"""
        line = '2013/04/14\t\tabc store'
        self.assertTrue(LedgerThing.is_transaction_start(line))

    def test_leading_white_space(self):
        """leading whitespace should return false"""
        line = '    2013/04/14 abc store'
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_date_only(self):
        """date only should return false"""
        line = '2013/04/14 '
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_empty_line(self):
        """empty line should return false"""
        line = ''
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_newline(self):
        """newline should return false"""
        line = '\n'
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_whitespace(self):
        """whitespace should return false"""
        line = '            \t    '
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_invalid_date(self):
        """invalid date should return false"""
        line = '2013/02/30 abc store'
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_invalid_date_format_month(self):
        """valid date but invalid (for ledger) date fmt returns false"""
        line = '2013/5/12 abc store'
        self.assertFalse(LedgerThing.is_transaction_start(line))

    def test_invalid_date_format_day(self):
        """valid date but invalid (for ledger) date fmt returns false"""
        line = '2013/06/1 abc store'
        self.assertFalse(LedgerThing.is_transaction_start(line))
