from datetime import date
from unittest import TestCase

import pytest

from .. import util
from .helpers import Redirector


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
        self.assertFalse(util.is_integer(None))
        self.assertFalse(util.is_integer(''))

    def test_get_amount_str(self):
        self.assertEqual('0.00', util.get_amount_str(-0.00000000000001))
        self.assertEqual('0.00', util.get_amount_str(0.000000000000001))
        self.assertEqual('0.01', util.get_amount_str(0.006))
        self.assertEqual('3.56', util.get_amount_str(3.56))
        self.assertEqual('3.56', util.get_amount_str(3.561111111111111))
        self.assertEqual('5.00', util.get_amount_str(5))

    def test_get_amount_str_num_decimals(self):
        self.assertEqual('0.0000', util.get_amount_str(-0.00000000000001, 4))
        self.assertEqual('0.00000', util.get_amount_str(0.000000000000001, 5))
        self.assertEqual('0.0060', util.get_amount_str(0.006000, 4))
        self.assertEqual('3.5679', util.get_amount_str(3.56789, 4))
        self.assertEqual('5.000000', util.get_amount_str(5, 6))
        self.assertEqual('0', util.get_amount_str(-0.0000001, 0))
        self.assertEqual('0', util.get_amount_str(0.0000001, 0))
        self.assertEqual('2', util.get_amount_str(1.8, 0))
        self.assertEqual('-3', util.get_amount_str(-3.2, 0))

    def test_get_colored_amount(self):
        self.assertEqual(
            '\x1b[0;32m$ 0.00\x1b[0m',
            util.get_colored_amount(-0.00000000000000000000001)
        )
        self.assertEqual(
            '\x1b[0;32m$ 0.00\x1b[0m',
            util.get_colored_amount(0.00000000000000000000001)
        )
        self.assertEqual(
            '\x1b[0;31m$ -3.14\x1b[0m',
            util.get_colored_amount(-3.14)
        )
        self.assertEqual(
            '\x1b[0;32m$ 3.14\x1b[0m',
            util.get_colored_amount(3.14)
        )
        self.assertEqual(
            '\x1b[0;31m$ -5.68\x1b[0m',
            util.get_colored_amount(-5.678)
        )
        self.assertEqual(
            '\x1b[0;32m$ 5.67\x1b[0m',
            util.get_colored_amount(5.672)
        )
        self.assertEqual(
            '\x1b[0;32m    $ 9.99\x1b[0m',
            util.get_colored_amount(9.99, column_width=10)
        )
        self.assertEqual(
            '\x1b[0;32m    $ 9.99\x1b[0m',
            util.get_colored_amount(9.99, column_width=10)
        )
        self.assertEqual(
            '\x1b[0;32m $ 9,999.99\x1b[0m',
            util.get_colored_amount(9999.99, column_width=11)
        )

    def test_get_colored_amount_for_shares(self):
        self.assertEqual(
            '\x1b[0;32m0.000000\x1b[0m',
            util.get_colored_amount(-0.00000000000000000000001, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;32m0.000000\x1b[0m',
            util.get_colored_amount(0.00000000000000000000001, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;31m-3.140000\x1b[0m',
            util.get_colored_amount(-3.14, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;32m3.140000\x1b[0m',
            util.get_colored_amount(3.14, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;31m-5.678988\x1b[0m',
            util.get_colored_amount(-5.6789876, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;32m5.672000\x1b[0m',
            util.get_colored_amount(5.672, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;32m        9.990000\x1b[0m',
            util.get_colored_amount(9.99, column_width=16, is_shares=True)
        )
        self.assertEqual(
            '\x1b[0;32m    9,999.990000\x1b[0m',
            util.get_colored_amount(9999.99, column_width=16, is_shares=True)
        )


@pytest.mark.parametrize('test_input, expected', [
    ([1.789], '$ 1.79'),
    ([1.789, 10, 3], '   $ 1.789'),
    ([-2.22, 10, 2], '   $ -2.22'),
    ([5.77, 5, 0], '  $ 6'),
])
def test_plain_dollar_amount(test_input, expected):
    assert util.get_plain_dollar_amount(*test_input) == expected


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


@pytest.mark.parametrize('test_input, expected', [
    (['1', '7', '2'], (1, 8)),
    ({'90', '7', '3'}, (3, 91)),
    (['1', '-7', '2'], (-7, 3)),
    (['-10', '-7', '-4'], (-10, -3)),
    ([2, 7, 1], (1, 8)),
    ({998, 7, 8}, (7, 999)),
])
def test_get_start_and_end_range_handled(test_input, expected):
    assert util.get_start_and_end_range(test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ([1, 7, 2], 14),
    ({9, 7, 3}, 189),
    ([], 1),
])
def test_product(test_input, expected):
    assert util.product(test_input) == expected
