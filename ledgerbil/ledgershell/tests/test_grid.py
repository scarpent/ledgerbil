import os
from textwrap import dedent
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
def test_get_column(mock_ledger_output):
    output = dedent('''\
                      $ 17.37  expenses: car: gas
                      $ 6.50  expenses: car: maintenance
                    $ 463.78  expenses: healthcare: medical insurance
        --------------------
                    $ 487.65
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': '17.37',
        'expenses: car: maintenance': '6.50',
        'expenses: healthcare: medical insurance': '463.78'
    }
    assert grid.get_column('boogy!') == expected


@mock.patch(__name__ + '.grid.get_column')
def test_main(mock_get_column):
    grid.main(['-l', 'hi'])
    mock_get_column.assert_called_once_with('hi')


@pytest.mark.parametrize('test_input, expected', [
    (['-a', 'blah or blarg'], 'blah or blarg'),
    (['--accounts', 'fu or bar'], 'fu or bar'),
    ([], None),
])
def test_args_accounts(test_input, expected):
    args = grid.get_args(test_input)
    assert args.accounts == expected
