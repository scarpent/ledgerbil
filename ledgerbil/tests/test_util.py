import sys
from datetime import date
from unittest import mock

import pytest

from .. import util


@pytest.mark.parametrize('test_input, expected', [
    ('-100', -100),
    ('2^6', 4),
    ('2**6', 64),
    ('1 + 2*3**(4^5) / (6 + -7)', -5),
    ('12*1.07275', 12.873000000000001),
    ('~1', -2),
])
def test_eval_expr(test_input, expected):
    assert util.eval_expr(test_input) == expected


def test_eval_expr_error():
    with pytest.raises(TypeError):
        util.eval_expr('a')


def test_get_date_string():
    assert util.get_date_string(date(1999, 12, 3)) == '1999/12/03'


def test_get_date_string_with_format():
    date_string = util.get_date_string(date(1999, 12, 3), the_format='%Y/%m')
    assert date_string == '1999/12'
    assert util.get_date_string(date(1999, 12, 3), '%Y') == '1999'


def test_get_date():
    assert util.get_date('1999/12/03') == date(1999, 12, 3)


def test_get_date_with_format():
    assert util.get_date('1999', the_format='%Y') == date(1999, 1, 1)
    assert util.get_date('1999/12', '%Y/%m') == date(1999, 12, 1)


@pytest.mark.parametrize('test_input, expected', [
    ('2016/10/26', True),
    ('2016/1/5', True),
    ('2016/5/5 10:23', False),
])
def test_is_valid_date(test_input, expected):
    assert util.is_valid_date(test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ('4', True),
    ('-4', True),
    ('+4', True),
    ('4.5', False),
    ('-4.5', False),
    ('+4.5', False),
    ('gooogly moogly', False),
    (None, False),
    ('', False),
])
def test_is_integer(test_input, expected):
    assert util.is_integer(test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ('$ -1,234.56', -1234.56),
    ('$ 567', 567),
    ('-789.2', -789.2),
    ('9876.54321', 9876.54321)
])
def test_get_float(test_input, expected):
    assert util.get_float(test_input) == expected


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


@pytest.mark.parametrize('test_input, expected', [
    ('', []),
    (None, []),
    ('a b "c d"', ['a', 'b', 'c d'])
])
def test_parse_args_good(test_input, expected):
    assert util.parse_args(test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ('"open', None),
    ('"still open', None),
    ("this also counts as open'", None)
])
def test_parse_args_bad(test_input, expected):
    expected_print = '*** No closing quotation'
    with mock.patch(__name__ + '.util.print') as mock_print:
        assert util.parse_args(test_input) == expected
    mock_print.assert_called_once_with(expected_print)


@pytest.mark.parametrize('test_input, expected', [
    ([-0.00000000000001], '0.00'),
    ([0.000000000000001], '0.00'),
    ([0.006], '0.01'),
    ([3.56], '3.56'),
    ([3.561111111111111], '3.56'),
    ([5], '5.00'),
    ([-0.00000000000001, 4], '0.0000'),
    ([0.000000000000001, 5], '0.00000'),
    ([0.006000, 4], '0.0060'),
    ([3.56789, 4], '3.5679'),
    ([5, 6], '5.000000'),
    ([-0.0000001, 0], '0'),
    ([0.0000001, 0], '0'),
    ([1.8, 0], '2'),
    ([-3.2, 0], '-3'),
])
def test_get_amount_str(test_input, expected):
    assert util.get_amount_str(*test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ([1.789], '$ 1.79'),
    ([1.789, 10, 3], '   $ 1.789'),
    ([-2.22, 10, 2], '   $ -2.22'),
    ([5.77, 5, 0], '  $ 6'),
    ([5.77, 5, 0, '€'], '   €6'),
])
def test_get_plain_amount(test_input, expected):
    assert util.get_plain_amount(*test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ([-0.00000000000000000000001], '\x1b[0;32m$ 0.00\x1b[0m'),
    ([0.00000000000000000000001], '\x1b[0;32m$ 0.00\x1b[0m'),
    ([-3.14], '\x1b[0;31m$ -3.14\x1b[0m'),
    ([3.14], '\x1b[0;32m$ 3.14\x1b[0m'),
    ([-5.678], '\x1b[0;31m$ -5.68\x1b[0m'),
    ([5.672], '\x1b[0;32m$ 5.67\x1b[0m'),
    ([9.99, 10], '\x1b[0;32m    $ 9.99\x1b[0m'),
    ([9999.99, 11], '\x1b[0;32m $ 9,999.99\x1b[0m'),
    ([1.56789, 1, 3], '\x1b[0;32m$ 1.568\x1b[0m'),
    ([-5.6789, 1, 5, '€'], '\x1b[0;31m€-5.67890\x1b[0m'),
    ([1.11, 1, 2, '# ', 'white'], '\x1b[0;37m# 1.11\x1b[0m'),
    ([-1.11, 1, 2, '# ', 'white'], '\x1b[0;31m# -1.11\x1b[0m'),
    ([0, 1, 2, '', 'white', 'purple'], '\x1b[0;35m0.00\x1b[0m'),
])
def test_get_colored_amount(test_input, expected):
    assert util.get_colored_amount(*test_input) == expected


@mock.patch(__name__ + '.util.print')
def test_handle_error(mock_print):
    return_value = util.handle_error('this is a test')
    assert return_value == -1
    mock_print.assert_called_once_with('this is a test', file=sys.stderr)
