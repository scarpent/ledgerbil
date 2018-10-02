import pytest

from .. import util


@pytest.mark.parametrize('test_input, expected', [
    ('         5.000 yyzxx  fu: bar',
        util.AccountBalance('fu: bar', 5.0, 'yyzxx')),
    ('             $ 17.37  car: gas',
        util.AccountBalance('car: gas', 17.37, '$')),
    ('abc', None),
])
def test_get_account_balance_generic(test_input, expected):
    assert util.get_account_balance_generic(test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    # shares=False is default, so this won't match
    (('         5.000 yyzxx  fu: bar', ), None),
    # if we specify shares=True, won't match on $
    (('             $ 17.37  car: gas', True), None),
    # not stripping the account
    (('        -5.000 yyzxx    fu: bar', True, False),
        util.AccountBalance('    fu: bar', -5.0, 'yyzxx')),
    (('$ -17.37  car: gas', False, False),
        util.AccountBalance('  car: gas', -17.37, '$')),
])
def test_get_account_balance_x(test_input, expected):
    assert util.get_account_balance(*test_input) == expected


@pytest.mark.parametrize('test_input, expected', [
    ('17-Feb-09 - 17-May-30   <Total>   $ 90.00   $ 90.00', 90.0),
    ('fubar', None),
    ('', None),
])
def test_get_payee_subtotal(test_input, expected):
    assert util.get_payee_subtotal(test_input) == expected
