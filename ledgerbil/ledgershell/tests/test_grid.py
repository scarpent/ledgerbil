import os
from unittest import mock

import pytest

from .. import grid, runner


class MockSettings(object):
    LEDGER_COMMAND = 'ledger'
    LEDGER_DIR = 'lmn'
    LEDGER_FILES = [
        'blarg.ldg',
        'glurg.ldg',
    ]
    PRICES_FILE = os.path.join(LEDGER_DIR, 'ijk')
    INVESTMENT_DEFAULT_ACCOUNTS = 'abc'
    INVESTMENT_DEFAULT_END_DATE = 'xyz'


def setup_module(module):
    grid.settings = MockSettings()
    runner.settings = MockSettings()


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_main(mock_ledger_output):
    grid.main(['-l', 'hi'])
    mock_ledger_output.assert_called_once_with('hi')


@pytest.mark.parametrize('test_input, expected', [
    (['-a', 'blah or blarg'], 'blah or blarg'),
    (['--accounts', 'fu or bar'], 'fu or bar'),
    ([], None),
])
def test_args_accounts(test_input, expected):
    args = grid.get_args(test_input)
    assert args.accounts == expected
