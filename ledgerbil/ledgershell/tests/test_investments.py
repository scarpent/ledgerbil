import os
from unittest import mock

from .. import investments


class TestSettings(object):
    INVESTMENT_DEFAULT_ACCOUNTS = 'abc'
    INVESTMENT_DEFAULT_END_DATE = 'xyz'
    LEDGER_DIR = 'lmn'
    PRICES_FILE = 'ijk'


@mock.patch(__name__ + '.investments.print')
def test_check_for_negative_dollars_no_warning(mock_print):
    investments.check_for_negative_dollars('$ 10', 'blah')
    assert not mock_print.called


@mock.patch(__name__ + '.investments.print')
def test_check_for_negative_dollars_warning(mock_print):
    expected = 'Negative dollar amount $ -10 for "blah."'
    investments.check_for_negative_dollars('$ -10', 'blah')
    output = investments.Colorable.get_plain_text(mock_print.call_args[0][0])
    assert expected in output


def test_get_investment_command_options_defaults():
    investments.settings = TestSettings()
    expected = '--market --price-db {prices} bal abc --end xyz'.format(
        prices=os.path.join(
            TestSettings.LEDGER_DIR,
            TestSettings.PRICES_FILE
        )
    )
    # It would be nice to test with actual defaults but they appear
    # to be set at import time so we'll do this
    actual = investments.get_investment_command_options(
        accounts=TestSettings.INVESTMENT_DEFAULT_ACCOUNTS,
        end_date=TestSettings.INVESTMENT_DEFAULT_END_DATE
    )
    assert actual == expected


def test_get_investment_command_options_defaults_plus_begin_date():
    investments.settings = TestSettings()
    expected = '--market --price-db {p} bal abc --begin qrt --end xyz'.format(
        p=os.path.join(
            TestSettings.LEDGER_DIR,
            TestSettings.PRICES_FILE
        )
    )
    actual = investments.get_investment_command_options(
        accounts=TestSettings.INVESTMENT_DEFAULT_ACCOUNTS,
        begin_date='qrt',
        end_date=TestSettings.INVESTMENT_DEFAULT_END_DATE
    )
    assert actual == expected


def test_get_lines():
    pass
