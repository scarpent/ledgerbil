import sys
from datetime import date
from textwrap import dedent
from unittest import mock

import pytest

from .. import grid, runner
from ...tests.helpers import OutputFileTester


class MockSettings:
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

    timestuff = '--begin banana --end eggplant --period pear'
    args, ledger_args = grid.get_args(f'{timestuff} lettuce'.split())

    assert grid.get_period_names(args, ledger_args) == (['2017', '2018'], None)
    mock_ledger_output.assert_called_once_with(
        f'register {timestuff} '
        '--yearly --date-format %Y --collapse --empty lettuce'.split()
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months(mock_ledger_output):
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0
    ''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args([
        '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', 'lettuce'
    ])
    actual = grid.get_period_names(args, ledger_args, 'month')
    assert actual == (['2017/11', '2017/12', '2018/01'], None)
    mock_ledger_output.assert_called_once_with([
        'register', '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', '--monthly', '--date-format', '%Y/%m',
        '--collapse', '--empty', 'lettuce'
    ])


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
    args, ledger_args = grid.get_args([
        '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', 'lettuce', '--current'
    ])
    actual = grid.get_period_names(args, ledger_args, 'month')
    assert actual == (['2017/11', '2017/12'], '2017/12')
    mock_ledger_output.assert_called_once_with([
        'register', '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', '--monthly', '--date-format', '%Y/%m',
        '--collapse', '--empty', 'lettuce'
    ])


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
    args, ledger_args = grid.get_args([
        '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', 'lettuce', '--current'
    ])
    actual = grid.get_period_names(args, ledger_args, 'month')
    assert actual == (['2017/11', '2017/12', '2018/01'], None)
    mock_ledger_output.assert_called_once_with([
        'register', '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', '--monthly', '--date-format', '%Y/%m',
        '--collapse', '--empty', 'lettuce'
    ])


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts(mock_ledger_output):
    output = dedent('''\
                     $ 17.37  expenses: car: gas
                      $ 6.50  expenses: car: maintenance
                  $ 1,001.78  expenses: widgets
        --------------------
                  $ 1,025.65
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
        'expenses: car: maintenance': 6.50,
        'expenses: widgets': 1001.78,
    }
    assert grid.get_column_accounts('2018', []) == expected
    mock_ledger_output.assert_called_once_with(
        ['balance', '--flat', '--period', '2018']
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_depth_one(mock_ledger_output):
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
    assert grid.get_column_accounts('2018', [], depth=1) == expected
    mock_ledger_output.assert_called_once_with(
        ['balance', '--flat', '--period', '2018']
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_depth_two(mock_ledger_output):
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
    assert grid.get_column_accounts('2018', [], depth=2) == expected
    mock_ledger_output.assert_called_once_with(
        ['balance', '--flat', '--period', '2018']
    )


@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_differing_totals(mock_ledger_output, mock_print):
    output = dedent('''\
                    $ 49.998  expenses: parent
                    $ 29.999  expenses: parent: child
        --------------------
                    $ 49.998
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: parent': 49.998,
        'expenses: parent: child': 29.999,
    }
    assert grid.get_column_accounts('2018', []) == expected
    mock_ledger_output.assert_called_once_with(
        ['balance', '--flat', '--period', '2018']
    )
    message = (
        "Warning: Differing total found between ledger's 49.998 and "
        "ledgerbil's 79.997 for --period 2018. Ledger's will be the correct "
        "total. This is mostly likely caused by funds being applied to both a "
        "parent and child account."
    )
    mock_print.assert_called_once_with(message, file=sys.stderr)


@mock.patch('builtins.sum')
@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_rounding(mock_ledger_output,
                                      mock_print,
                                      mock_sum):
    """should not warn about total differences that round to same dollar"""
    # can get much smaller rounding differences if calculations used
    # in ledger data; but don't want to set up that test right now,
    # and we're rounding to the dollar because that seems close enough
    output = dedent('''\
                     $ 17.37  expenses: car: gas
                      $ 6.50  expenses: car: maintenance
        --------------------
                     $ 23.87
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
        'expenses: car: maintenance': 6.50,
    }
    mock_sum.return_value = 23.55
    assert grid.get_column_accounts('2018', []) == expected
    mock_ledger_output.assert_called_once_with(
        ['balance', '--flat', '--period', '2018']
    )
    mock_print.assert_not_called()


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_no_total(mock_ledger_output):
    output = dedent('''\
                     $ 17.37  expenses: car: gas
    ''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
    }
    assert grid.get_column_accounts('2018', []) == expected
    mock_ledger_output.assert_called_once_with(
        ['balance', '--flat', '--period', '2018']
    )


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
    assert grid.get_column_payees('blah', ['bogus']) == expected
    mock_ledger_output.assert_called_once_with(
        ['register', 'expenses', '--group-by', '(payee)', '--collapse',
         '--subtotal', '--depth', '1', '--period', 'blah', 'bogus']
    )


@mock.patch(__name__ + '.grid.get_column_payees')
def test_get_columns_payees(mock_get_column_payees):
    bratwurst_column = {'zig': 17.37, 'zag': 6.50}
    knockwurst_column = {'blitz': 28.19, 'krieg': 500.10}
    mock_get_column_payees.side_effect = [bratwurst_column, knockwurst_column]

    expected_columns = {
        'bratwurst': bratwurst_column,
        'knockwurst': knockwurst_column,
    }
    expected_payees = {'zig', 'zag', 'blitz', 'krieg'}

    payees, columns = grid.get_columns(
        ['bratwurst', 'knockwurst'],
        ['?', '!'],
        payees=True
    )
    assert payees == expected_payees
    assert columns == expected_columns
    mock_get_column_payees.assert_has_calls([
        mock.call('bratwurst', ['?', '!']),
        mock.call('knockwurst', ['?', '!']),
    ])


@mock.patch(__name__ + '.grid.get_column_accounts')
def test_get_columns(mock_get_column_accounts):
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
    mock_get_column_accounts.side_effect = [lemon_column, lime_column]

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
    mock_get_column_accounts.assert_has_calls([
        mock.call('lemon', ['salt!'], 0),
        mock.call('lime', ['salt!'], 0),
    ])


@mock.patch(__name__ + '.grid.get_column_accounts')
def test_get_columns_with_current(mock_get_column_accounts):
    lemon_column = {'expenses: widgets': 1001.78}
    lime_column = {'expenses: unicorns': -10123.55}
    mock_get_column_accounts.side_effect = [lemon_column, lime_column]

    expected_columns = {'lemon': lemon_column, 'lime': lime_column}
    expected_accounts = {'expenses: unicorns', 'expenses: widgets'}

    accounts, columns = grid.get_columns(
        ['lemon', 'lime'],
        ['salt!'],
        current='lime'
    )
    assert accounts == expected_accounts
    assert columns == expected_columns
    mock_get_column_accounts.assert_has_calls([
        mock.call('lemon', ['salt!'], 0),
        mock.call('lime', ['salt!', '--end', 'tomorrow'], 0),
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


expected_sort_rows_by_total = [
    (90, 50, 140, 'expenses: widgets'),
    (100, 10, 110, 'expenses: car: gas'),
    (0, 20, 20, 'expenses: unicorns'),
    (-50, 0, -50, 'expenses: car: maintenance'),
    (140, 80, 220),
]

expected_sort_rows_by_row_header = [
    (100, 10, 110, 'expenses: car: gas'),
    (-50, 0, -50, 'expenses: car: maintenance'),
    (0, 20, 20, 'expenses: unicorns'),
    (90, 50, 140, 'expenses: widgets'),
    (140, 80, 220),
]

expected_sort_rows_by_column_header = [
    (90, 50, 140, 'expenses: widgets'),
    (0, 20, 20, 'expenses: unicorns'),
    (100, 10, 110, 'expenses: car: gas'),
    (-50, 0, -50, 'expenses: car: maintenance'),
    (140, 80, 220),
]

expected_sort_rows_by_total_with_limit = [
    (90, 50, 140, 'expenses: widgets'),
    (100, 10, 110, 'expenses: car: gas'),
    (190, 60, 250),
]


@pytest.mark.parametrize('test_input, expected', [
    ((grid.SORT_DEFAULT, 0), expected_sort_rows_by_total),
    (('unrecognized', 0), expected_sort_rows_by_total),
    (('row', 0), expected_sort_rows_by_row_header),
    (('lime', 0), expected_sort_rows_by_column_header),
    ((grid.SORT_DEFAULT, 2), expected_sort_rows_by_total_with_limit),
])
@mock.patch(__name__ + '.grid.get_grid')
def test_get_rows(mock_get_grid, test_input, expected):
    mock_get_grid.return_value = {
        'expenses: car: gas': {'lemon': 100, 'lime': 10},
        'expenses: car: maintenance': {'lemon': -50},
        'expenses: unicorns': {'lime': 20},
        'expenses: widgets': {'lemon': 90, 'lime': 50},
    }
    row_headers = {
        'expenses: car: gas',
        'expenses: car: maintenance',
        'expenses: unicorns',
        'expenses: widgets'
    }
    columns = None  # accounted for in mock grid return value
    period_names = ['lemon', 'lime']
    sort, limit = test_input
    actual = grid.get_rows(row_headers, columns, period_names, sort, limit)
    assert actual == [('lemon', 'lime', grid.SORT_DEFAULT)] + expected


@mock.patch(__name__ + '.grid.get_grid')
def test_get_rows_single_column_sort_total(mock_get_grid):
    mock_get_grid.return_value = {
        'expenses: unicorns': {'mango': 50},
        'expenses: widgets': {'mango': 70},
    }
    row_headers = {'expenses: unicorns', 'expenses: widgets'}
    columns = None  # accounted for in mock grid return value
    period_names = ['mango']
    actual = grid.get_rows(row_headers, columns, period_names, 'total', 0)
    expected = [
        ('mango', ),
        (70, 'expenses: widgets'),
        (50, 'expenses: unicorns'),
        (120, ),
    ]
    assert actual == expected


@mock.patch(__name__ + '.grid.get_grid')
def test_get_rows_single_column_sort_row(mock_get_grid):
    mock_get_grid.return_value = {
        'expenses: widgets': {'mango': 70},
        'expenses: unicorns': {'mango': 50},
    }
    row_headers = {'expenses: unicorns', 'expenses: widgets'}
    columns = None  # accounted for in mock grid return value
    period_names = ['mango']
    actual = grid.get_rows(row_headers, columns, period_names, 'row', 0)
    expected = [
        ('mango', ),
        (50, 'expenses: unicorns'),
        (70, 'expenses: widgets'),
        (120, ),
    ]
    assert actual == expected


def test_get_flat_report():
    rows = [
        ('lemon', 'lime', grid.SORT_DEFAULT),
        (2.65, 500.1, 502.75, 'expenses: widgets'),
        (17.37, 28.19, 45.56, 'expenses: car: gas'),
        (6.5, 0, 6.5, 'expenses: car: maintenance'),
        (0, -10123.55, -10123.55, 'expenses: unicorns'),
        (26.52, -9595.26, -9568.74),
    ]
    report = grid.get_flat_report(rows)
    helper = OutputFileTester(f'test_grid_flat_report')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_month(mock_pnames, mock_cols, mock_rows, mock_report):
    period_names, row_headers, columns, rows, flat_report = (
        ['garlic', 'paprika'], 'fennel', 'tarragon', ['basil'], 'parsley',
    )

    mock_pnames.return_value = (period_names, None)
    mock_cols.return_value = (row_headers, columns)
    mock_rows.return_value = rows
    mock_report.return_value = flat_report

    args, ledger_args = grid.get_args(['--month', 'nutmeg'])
    assert grid.get_grid_report(args, ledger_args) == flat_report
    mock_pnames.assert_called_once_with(args, ledger_args, 'month')
    mock_cols.assert_called_once_with(
        period_names,
        ledger_args,
        depth=0,
        current=None,
        payees=False
    )
    mock_rows.assert_called_once_with(
        row_headers, columns, period_names, grid.SORT_DEFAULT, 0
    )
    mock_report.assert_called_once_with(rows)


@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_year(mock_pnames, mock_cols, mock_rows, mock_report):
    # this test wants to make sure unit was set correctly, along
    # with passing through args depth, payee, and limit appropriately
    period_names, row_headers, columns, flat_report = (
        {'paprika', 'garglic'}, 'fennel', 'tarragon', 'parsley',
    )

    mock_pnames.return_value = (period_names, 'celery')
    mock_cols.return_value = (row_headers, columns)
    mock_report.return_value = flat_report

    # -y defaults to True so could also be a test without -y and -m
    args, ledger_args = grid.get_args([
        '--year', 'nutmeg', '--depth', '5', '--limit', '20',
        '--payee', '--sort', 'cloves'
    ])
    assert grid.get_grid_report(args, ledger_args) == flat_report
    mock_pnames.assert_called_once_with(args, ledger_args, 'year')
    mock_cols.assert_called_once_with(
        period_names,
        ledger_args,
        depth=5,
        current='celery',
        payees=True
    )
    mock_rows.assert_called_once_with(
        row_headers, columns, period_names, 'cloves', 20
    )


@mock.patch(__name__ + '.grid.get_ledger_output', return_value='')
def test_get_grid_report_no_period_names(mock_ledger_output):
    # no results from initial ledger query for periods
    args, ledger_args = grid.get_args([])
    assert grid.get_grid_report(args, ledger_args) == ''


@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_no_results(mock_pnames, mock_cols, mock_rows):
    period_names, row_headers, columns = (
        {'paprika', 'garglic'}, 'fennel', 'tarragon',
    )

    mock_pnames.return_value = (period_names, 'celery')
    mock_cols.return_value = (row_headers, columns)
    mock_rows.return_value = [('2016', '2017', '2018', 'total'), ()]

    args, ledger_args = grid.get_args([])
    assert grid.get_grid_report(args, ledger_args) == ''


@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_grid_report')
def test_main(mock_get_grid_report, mock_print):
    mock_get_grid_report.return_value = 'bananas!'
    args, unknown = grid.get_args(['-y', 'xyz'])
    grid.main(['-y', 'xyz'])
    mock_get_grid_report.assert_called_once_with(args, ['xyz'])
    mock_print.assert_called_once_with('bananas!', end='')


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
    (['--payees'], True),
    ([], False),
])
def test_args_payees(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.payees == expected


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
    (['--limit', '30'], 30),
    ([], 0),
])
def test_args_limit(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.limit == expected


@pytest.mark.parametrize('test_input, expected', [
    (['-s', '2007'], '2007'),
    (['--sort', '12/2009'], '12/2009'),
    ([], 'total'),
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
