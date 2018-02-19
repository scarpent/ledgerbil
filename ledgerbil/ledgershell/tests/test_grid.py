from textwrap import dedent
from unittest import mock

import pytest

from .. import grid, runner


class MockSettings(object):
    LEDGER_COMMAND = ['ledger']
    LEDGER_DIR = 'lmn'
    LEDGER_FILES = [
        'blarg.ldg',
        'glurg.ldg',
    ]


def setup_module(module):
    grid.settings = MockSettings()
    runner.settings = MockSettings()


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_included_periods_years(mock_ledger_output):
    output = dedent('''\
        2017 - 2017          <Total>                    0         0
        2018 - 2018          <Total>                    0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args(
        ['-b', 'banana', '-e', 'eggplant', '-p', 'pear', 'lettuce']
    )
    assert grid.get_included_periods(args, ledger_args) == {'2017', '2018'}
    mock_ledger_output.assert_called_once_with(
        ['reg', '-b', 'banana', '-e', 'eggplant', '-p', 'pear',
         '--yearly', '-y', '%Y', '--collapse', '--empty', 'lettuce']
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_included_periods_months(mock_ledger_output):
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args(
        ['-b', 'banana', '-e', 'eggplant', '-p', 'pear', 'lettuce']
    )
    actual_months = grid.get_included_periods(args, ledger_args, 'month')
    assert actual_months == {'2017/11', '2017/12', '2018/01'}
    mock_ledger_output.assert_called_once_with(
        ['reg', '-b', 'banana', '-e', 'eggplant', '-p', 'pear',
         '--monthly', '-y', '%Y/%m', '--collapse', '--empty', 'lettuce']
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column(mock_ledger_output):
    output = dedent('''\
                     $ 17.37  expenses: car: gas
                      $ 6.50  expenses: car: maintenance
                  $ 1,001.78  expenses: widgets
        --------------------
                    $ 487.65
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
        'expenses: car: maintenance': 6.50,
        'expenses: widgets': 1001.78
    }
    assert grid.get_column(['boogy!']) == expected
    mock_ledger_output.assert_called_once_with(['boogy!'])


@mock.patch(__name__ + '.grid.get_grid_report')
def test_main(mock_get_grid_report):
    args, unknown = grid.get_args(['-y', 'xyz'])
    grid.main(['-y', 'xyz'])
    mock_get_grid_report.assert_called_once_with(args, ['xyz'])


@pytest.mark.parametrize('test_input, expected', [
    (['-y'], True),
    (['--year'], True),
    ([], True),
])
def test_args_year(test_input, expected):
    args, ledger_args = grid.get_args(test_input)
    assert args.year == expected
    assert ledger_args == []


@pytest.mark.parametrize('test_input, expected', [
    (['-m'], True),
    (['--month'], True),
    ([], False),
])
def test_args_month(test_input, expected):
    args, ledger_args = grid.get_args(test_input)
    assert args.month == expected
    assert ledger_args == []


def test_args_year_and_month_are_mutually_exclusive():
    with pytest.raises(SystemExit) as excinfo:
        grid.get_args(['--month', '--year'])
    assert str(excinfo.value) == '2'


@pytest.mark.parametrize('test_input, expected', [
    (['-b', 'today'], 'today'),
    (['--begin', '2016/01/12'], '2016/01/12'),
    ([], None),
])
def test_args_begin_date(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.begin == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-e', 'yesterday'], 'yesterday'),
    (['--end', '2017/10/05'], '2017/10/05'),
    ([], None),
])
def test_args_end_date(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.end == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-p', 'yesterday'], 'yesterday'),
    (['--period', '2017'], '2017'),
    ([], None),
])
def test_args_period(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.period == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-m', 'a', 'b', '-c'], ['a', 'b', '-c']),
    (['a', 'b', '-c'], ['a', 'b', '-c']),
    ([], []),
])
def test_ledger_args(test_input, expected):
    args, ledger_args = grid.get_args(test_input)
    assert ledger_args == expected


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_main_temporary_test(mock_ledger_output):
    grid.main(['-l', 'bal expenses --flat'])
    mock_ledger_output.assert_called_once_with(['bal', 'expenses', '--flat'])
