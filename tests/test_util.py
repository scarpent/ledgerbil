#!/usr/bin/env python

from datetime import date
from unittest import TestCase

import util

from helpers import Redirector


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class UtilTests(TestCase):

    def test_eval_expr(self):
        self.assertEqual(-100, util.eval_expr('-100'))
        self.assertEqual(4, util.eval_expr('2^6'))
        self.assertEqual(64, util.eval_expr('2**6'))
        self.assertEqual(
            -5,
            util.eval_expr('1 + 2*3**(4^5) / (6 + -7)')
        )
        self.assertEqual(
            12.873000000000001,
            util.eval_expr('12*1.07275')
        )
        self.assertEqual(-2, util.eval_expr('~1'))  # invert
        with self.assertRaises(TypeError):
            util.eval_expr('a')

    def test_dates(self):
        self.assertEqual(
            '1999/12/03',
            util.get_date_string(date(1999, 12, 3))
        )
        self.assertEqual(
            date(1999, 12, 3),
            util.get_date('1999/12/03')
        )
        self.assertTrue(util.is_valid_date('2016/10/26'))
        self.assertTrue(util.is_valid_date('2016/1/5'))
        self.assertFalse(util.is_valid_date('2016/5/5 10:23'))

    def test_is_integer(self):
        self.assertTrue(util.is_integer('4'))
        self.assertTrue(util.is_integer('-4'))
        self.assertTrue(util.is_integer('+4'))
        self.assertFalse(util.is_integer('4.5'))
        self.assertFalse(util.is_integer('-4.5'))
        self.assertFalse(util.is_integer('+4.5'))
        self.assertFalse(util.is_integer('gooogly moogly'))


class OutputTests(Redirector):

    def test_parse_args_open_quote(self):
        output = '*** No closing quotation'
        result = util.parse_args('"open')
        self.assertIsNone(result)
        self.assertEqual(output, self.redirect.getvalue().rstrip())
        self.reset_redirect()
        util.parse_args("'still open")
        self.assertEqual(output, self.redirect.getvalue().rstrip())
        self.reset_redirect()
        util.parse_args("this also counts as open'")
        self.assertEqual(output, self.redirect.getvalue().rstrip())

    def test_parse_args_good(self):
        args = util.parse_args('')
        self.assertEqual([], args)
        args = util.parse_args(None)
        self.assertEqual([], args)
        args = util.parse_args('a b "c d"')
        self.assertEqual(['a', 'b', 'c d'], args)
