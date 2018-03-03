from datetime import date
from textwrap import dedent
from unittest import mock

import pytest

from .. import grid, runner
from ...tests.helpers import OutputFileTester


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
def test_get_period_names_years(mock_ledger_output):
    output = dedent('''\
        2017 - 2017          <Total>                    0         0
        2018 - 2018          <Total>                    0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args(
        ['-b', 'banana', '-e', 'eggplant', '-p', 'pear', 'lettuce']
    )
    expected = (['2017', '2018'], None)
    assert grid.get_period_names(args, ledger_args) == expected
    mock_ledger_output.assert_called_once_with(
        ['register', '-b', 'banana', '-e', 'eggplant', '-p', 'pear',
         '--yearly', '-y', '%Y', '--collapse', '--empty', 'lettuce']
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months(mock_ledger_output):
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args(
        ['-b', 'banana', '-e', 'eggplant', '-p', 'pear', 'lettuce']
    )
    actual = grid.get_period_names(args, ledger_args, 'month')
    assert actual == (['2017/11', '2017/12', '2018/01'], None)
    mock_ledger_output.assert_called_once_with(
        ['register', '-b', 'banana', '-e', 'eggplant', '-p', 'pear',
         '--monthly', '-y', '%Y/%m', '--collapse', '--empty', 'lettuce']
    )


@mock.patch(__name__ + '.grid.date')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months_with_current(mock_ledger_output, mock_date):
    mock_date.today.return_value = date(2017, 12, 15)
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args(
        ['-b', 'banana', '-e', 'egg', '-p', 'pear', 'lettuce', '--current']
    )
    actual = grid.get_period_names(args, ledger_args, 'month')
    assert actual == (['2017/11', '2017/12'], '2017/12')
    mock_ledger_output.assert_called_once_with(
        ['register', '-b', 'banana', '-e', 'egg', '-p', 'pear',
         '--monthly', '-y', '%Y/%m', '--collapse', '--empty', 'lettuce']
    )


@mock.patch(__name__ + '.grid.date')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months_with_current_not_found(mock_ledger_output,
                                                        mock_date):
    mock_date.today.return_value = date(2019, 12, 15)
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args(
        ['-b', 'banana', '-e', 'egg', '-p', 'pear', 'lettuce', '--current']
    )
    actual = grid.get_period_names(args, ledger_args, 'month')
    assert actual == (['2017/11', '2017/12', '2018/01'], None)
    mock_ledger_output.assert_called_once_with(
        ['register', '-b', 'banana', '-e', 'egg', '-p', 'pear',
         '--monthly', '-y', '%Y/%m', '--collapse', '--empty', 'lettuce']
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column(mock_ledger_output):
    output = dedent('''\
                     $ 17.37  expenses: car: gas
                      $ 6.50  expenses: car: maintenance
                  $ 1,001.78  expenses: widgets
        --------------------
                  $ 1,025.55
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
        'expenses: car: maintenance': 6.50,
        'expenses: widgets': 1001.78,
    }
    assert grid.get_column(['boogy!']) == expected
    mock_ledger_output.assert_called_once_with(['boogy!'])


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_depth_one(mock_ledger_output):
    output = dedent('''\
                     $ 10.00  apple: banana: cantaloupe
                     $ 20.00  apple: banana: eggplant
                     $ 40.00  grape: kiwi
                     $ 80.00  grape: fig
        --------------------
                    $ 150.00
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'apple': 30,
        'grape': 120,
    }
    assert grid.get_column(['boogy!'], depth=1) == expected
    mock_ledger_output.assert_called_once_with(['boogy!'])


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_depth_two(mock_ledger_output):
    output = dedent('''\
                     $ 10.00  apple: banana: cantaloupe
                     $ 20.00  apple: banana: eggplant
                     $ 40.00  grape:kiwi
                     $ 80.00  grape:fig
        --------------------
                    $ 150.00
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'apple: banana': 30,
        'grape:kiwi': 40,
        'grape:fig': 80,
    }
    assert grid.get_column(['boogy!'], depth=2) == expected
    mock_ledger_output.assert_called_once_with(['boogy!'])


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_payees(mock_ledger_output):
    output = dedent('''\
        food and stuff
        17-Nov-01 - 18-Jan-05    <Total>      $ 102.03           $ 102.03

        gas n go
        18-Jan-03 - 18-Jan-03    <Total>       $ 23.87            $ 23.87

        johnny paycheck
        17-Nov-15 - 17-Nov-30    <Total>    $ 1,381.32         $ 1,381.32

        jurassic fork
        18-Jan-08 - 18-Jan-08    <Total>       $ 42.17            $ 42.17\
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'food and stuff': 102.03,
        'gas n go': 23.87,
        'johnny paycheck': 1381.32,
        'jurassic fork': 42.17
    }
    assert grid.get_column_payees(['bogus']) == expected
    mock_ledger_output.assert_called_once_with(
        ['register', 'expenses', '--group-by', '(payee)',
         '--collapse', '--subtotal', '--depth', '1', 'bogus']
    )


@mock.patch(__name__ + '.grid.get_column')
def test_get_columns(mock_get_column):
    lemon_column = {
        'expenses: car: gas': 17.37,
        'expenses: car: maintenance': 6.50,
        'expenses: widgets': 1001.78,
    }
    lime_column = {
        'expenses: car: gas': 28.19,
        'expenses: widgets': 500.10,
        'expenses: unicorns': -10123.55,
    }
    mock_get_column.side_effect = [lemon_column, lime_column]

    expected_columns = {'lemon': lemon_column, 'lime': lime_column}
    expected_accounts = {
        'expenses: car: gas',
        'expenses: car: maintenance',
        'expenses: unicorns',
        'expenses: widgets',
    }

    accounts, columns = grid.get_columns(['lemon', 'lime'], ['salt!'])
    assert accounts == expected_accounts
    assert columns == expected_columns
    mock_get_column.assert_has_calls([
        mock.call(['balance', '--flat', '-p', 'lemon', 'salt!'], 0),
        mock.call(['balance', '--flat', '-p', 'lime', 'salt!'], 0),
    ])


@mock.patch(__name__ + '.grid.get_column')
def test_get_columns_with_current(mock_get_column):
    lemon_column = {'expenses: widgets': 1001.78}
    lime_column = {'expenses: unicorns': -10123.55}
    mock_get_column.side_effect = [lemon_column, lime_column]

    expected_columns = {'lemon': lemon_column, 'lime': lime_column}
    expected_accounts = {'expenses: unicorns', 'expenses: widgets'}

    accounts, columns = grid.get_columns(
        ['lemon', 'lime'],
        ['salt!'],
        current='lime'
    )
    assert accounts == expected_accounts
    assert columns == expected_columns
    mock_get_column.assert_has_calls([
        mock.call(['balance', '--flat', '-p', 'lemon', 'salt!'], 0),
        mock.call(
            ['balance', '--flat', '-p', 'lime', 'salt!', '-e', 'tomorrow'],
            0
        ),
    ])


def test_get_grid():
    accounts = {
        'expenses: car: gas',
        'expenses: car: maintenance',
        'expenses: unicorns',
        'expenses: widgets'
    }
    columns = {
        'lemon': {
            'expenses: car: gas': 17.37,
            'expenses: car: maintenance': 6.50,
            'expenses: widgets': 1001.78,
        },
        'lime': {
            'expenses: car: gas': 28.19,
            'expenses: widgets': 500.10,
            'expenses: unicorns': -10123.55,
        },
    }
    expected = {
        'expenses: car: gas': {'lemon': 17.37, 'lime': 28.19},
        'expenses: car: maintenance': {'lemon': 6.50},
        'expenses: unicorns': {'lime': -10123.55},
        'expenses: widgets': {'lemon': 1001.78, 'lime': 500.10},
    }
    assert grid.get_grid(accounts, columns) == expected


def test_get_flat_report_sort_default():
    run_get_flat_report('account')


def test_get_flat_report_sort_total():
    run_get_flat_report('total')


def test_get_flat_report_sort_column():
    run_get_flat_report('lemon')


def test_get_flat_report_sort_unrecognized():
    # Will sort by account if sort key is unrecognized
    run_get_flat_report('unrecognized')


def run_get_flat_report(sort):
    grid_x = {
        'expenses: car: gas': {'lemon': 17.37, 'lime': 28.19},
        'expenses: car: maintenance': {'lemon': 6.50},
        'expenses: unicorns': {'lime': -10123.55},
        'expenses: widgets': {'lemon': 2.65, 'lime': 500.10},
    }
    accounts = {
        'expenses: car: gas',
        'expenses: car: maintenance',
        'expenses: unicorns',
        'expenses: widgets'
    }
    columns = {
        'lemon': {
            'expenses: car: gas': 17.37,
            'expenses: car: maintenance': 6.50,
            'expenses: widgets': 2.65,
        },
        'lime': {
            'expenses: car: gas': 28.19,
            'expenses: widgets': 500.10,
            'expenses: unicorns': -10123.55,
        },
    }
    period_names = ['lime', 'lemon']

    report = grid.get_flat_report(
        grid_x,
        accounts,
        columns,
        period_names,
        sort
    )
    helper = OutputFileTester(f'test_grid_flat_report_sort_{sort}')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_grid')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_month(mock_pnames, mock_cols, mock_grid, mock_report):
    period_names, accounts, columns, grid_x, flat_report = (
        ['garlic', 'paprika'], 'fennel', 'tarragon', 'basil', 'parsley',
    )

    mock_pnames.return_value = (period_names, None)
    mock_cols.return_value = (accounts, columns)
    mock_grid.return_value = grid_x
    mock_report.return_value = flat_report

    args, ledger_args = grid.get_args(['--month', 'nutmeg'])
    assert grid.get_grid_report(args, ledger_args) == flat_report
    mock_pnames.assert_called_once_with(args, ledger_args, 'month')
    mock_cols.assert_called_once_with(
        period_names,
        ledger_args,
        depth=0,
        current=None,
    )
    mock_grid.assert_called_once_with(accounts, columns)
    mock_report.assert_called_once_with(
        grid_x, accounts, columns, sorted(period_names), 'account'
    )


@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_grid')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_year(mock_pnames, mock_cols, mock_grid, mock_report):
    # this test just wants to make sure unit was set correctly
    period_names, accounts, columns, flat_report = (
        {'paprika', 'garglic'}, 'fennel', 'tarragon', 'parsley',
    )

    mock_pnames.return_value = period_names
    mock_cols.return_value = (accounts, columns)
    mock_report.return_value = flat_report

    # -y defaults to True so could also be a test without -y and -m
    args, ledger_args = grid.get_args(['--year', 'nutmeg'])
    assert grid.get_grid_report(args, ledger_args) == flat_report
    mock_pnames.assert_called_once_with(args, ledger_args, 'year')


@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_grid_report')
def test_main(mock_get_grid_report, mock_print):
    mock_get_grid_report.return_value = 'bananas!'
    args, unknown = grid.get_args(['-y', 'xyz'])
    grid.main(['-y', 'xyz'])
    mock_get_grid_report.assert_called_once_with(args, ['xyz'])
    mock_print.assert_called_once_with('bananas!')


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
    (['--payee'], True),
    ([], False),
])
def test_args_payee(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.payee == expected


@pytest.mark.parametrize('test_input, expected', [
    (['--current'], True),
    ([], False),
])
def test_args_current(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.current == expected


@pytest.mark.parametrize('test_input, expected', [
    (['--depth', '2'], 2),
    ([], 0),
])
def test_args_depth(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.depth == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-s', '2007'], '2007'),
    (['--sort', '12/2009'], '12/2009'),
    ([], 'account'),
])
def test_args_sort(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.sort == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-m', 'a', 'b', '-c'], ['a', 'b', '-c']),
    (['a', 'b', '-c'], ['a', 'b', '-c']),
    ([], []),
])
def test_ledger_args(test_input, expected):
    args, ledger_args = grid.get_args(test_input)
    assert ledger_args == expected
