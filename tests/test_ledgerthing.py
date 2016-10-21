#!/usr/bin/python

"""unit test for ledgerthing.py"""

from unittest import TestCase

from datetime import date

from ledgerthing import LedgerThing
from ledgerthing import UNSPECIFIED_PAYEE


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Constructor(TestCase):

    def test_non_transaction_date(self):
        """non-transactions initially have date = None"""
        thing = LedgerThing(['blah', 'blah blah blah'])
        self.assertIsNone(thing.thing_date)

    def test_transaction_date(self):
        thing = LedgerThing(['2013/05/18 blah', '    ; something...'])
        self.assertEqual(thing.thing_date, date(2013, 5, 18))

    def verify_top_line(self, line, the_date, code, payee):
        thing = LedgerThing([line])
        self.assertEqual(thing.thing_date, the_date)
        if code is None:
            self.assertIsNone(thing.transaction_code)
        else:
            self.assertEqual(code, thing.transaction_code)
        self.assertEqual(payee, thing.payee)

    def test_top_line(self):
        self.verify_top_line(
            '2016/10/20',
            date(2016, 10, 20), '', UNSPECIFIED_PAYEE
        )
        self.verify_top_line(
            '2016/10/20 someone',
            date(2016, 10, 20), '', 'someone'
        )
        self.verify_top_line(
            '2016/10/20 someone           ; some comment',
            date(2016, 10, 20), '', 'someone'
        )
        self.verify_top_line(
            '2016/02/04 (123)',
            date(2016, 2, 4), '123', UNSPECIFIED_PAYEE
        )
        self.verify_top_line(
            '2016/02/04 (123) someone',
            date(2016, 2, 4), '123', 'someone'
        )
        self.verify_top_line(
            '2001/04/11 (abc)                 ; yah',
            date(2001, 4, 11), 'abc', UNSPECIFIED_PAYEE
        )
        self.verify_top_line(
            '2001/04/11 (abc) someone        ; yah',
            date(2001, 4, 11), 'abc', 'someone'
        )
        self.verify_top_line('2001/04/11(abc)', None, '', None)
        self.verify_top_line('2001/04/11someone', None, '', None)


class GetLines(TestCase):

    def test_get_lines(self):
        """lines can be entered and retrieved as is"""
        lines = ['abc\n', 'xyz\n']
        thing = LedgerThing(lines)
        self.assertEqual(lines, thing.get_lines())


class IsNewThing(TestCase):

    def test_is_new_thing(self):
        self.assertTrue(LedgerThing.is_new_thing('2013/04/15 ab store'))

    def test_is_not_thing(self):
        self.assertFalse(LedgerThing.is_new_thing(''))


class IsTransactionStart(TestCase):

    def test_valid_transaction_start(self):
        """date recognized as the start of a transaction"""
        self.assertTrue(
            LedgerThing.is_transaction_start('2013/04/14 abc store')
        )

    def test_valid_transaction_start_with_tabs(self):
        """date recognized as the start of a transaction"""
        self.assertTrue(
            LedgerThing.is_transaction_start('2013/04/14\t\tabc store')
        )

    def test_leading_white_space(self):
        """leading whitespace should return false"""
        self.assertFalse(
            LedgerThing.is_transaction_start('    2013/04/14 abc store')
        )

    def test_date_only(self):
        self.assertTrue(LedgerThing.is_transaction_start('2013/04/14 '))
        self.assertTrue(LedgerThing.is_transaction_start('2013/04/14'))

    def test_empty_line(self):
        self.assertFalse(LedgerThing.is_transaction_start(''))

    def test_newline(self):
        line = '\n'
        self.assertFalse(
            LedgerThing.is_transaction_start(line)
        )

    def test_whitespace(self):
        self.assertFalse(
            LedgerThing.is_transaction_start('            \t    ')
        )

    def test_invalid_date(self):
        self.assertFalse(
            LedgerThing.is_transaction_start('2013/02/30 abc store')
        )

    def test_invalid_date_formats(self):
        self.assertFalse(
            LedgerThing.is_transaction_start('2013/5/12 abc store')
        )
        self.assertFalse(
            LedgerThing.is_transaction_start('2013/06/1 abc store')
        )

    def test_transaction_code(self):
        self.assertTrue(
            LedgerThing.is_transaction_start('2016/10/20 (123) store')
        )
        self.assertTrue(
            LedgerThing.is_transaction_start('2016/10/20 (abc)store')
        )
        self.assertTrue(
            LedgerThing.is_transaction_start('2016/10/20 (123)')
        )
        self.assertTrue(
            LedgerThing.is_transaction_start('2016/10/20 (123)   ; xyz')
        )
        self.assertFalse(
            LedgerThing.is_transaction_start('2016/10/20(123)')
        )
        self.assertFalse(
            LedgerThing.is_transaction_start('2016/10/20someone')
        )
