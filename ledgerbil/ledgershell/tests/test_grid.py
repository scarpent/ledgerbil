import sys
from datetime import date
from textwrap import dedent
from unittest import mock

import pytest

from .. import grid
from ...colorable import Colorable
from ...tests.helpers import OutputFileTester


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_years(mock_ledger_output):
    output = dedent('''\
        2017 - 2017          <Total>                    0         0
        2018 - 2018          <Total>                    0         0''')
    mock_ledger_output.return_value = output

    timestuff = '--begin banana --end eggplant --period pear'
    args, ledger_args = grid.get_args(f'{timestuff} lettuce'.split())
    expected = (('2017', '2018'), None)
    actual = grid.get_period_names(args, tuple(ledger_args))
    assert actual == expected
    mock_ledger_output.assert_called_once_with(tuple(
        f'register {timestuff} --yearly --date-format %Y '
        '--collapse --empty lettuce'.split()
    ))


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months(mock_ledger_output):
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args([
        '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', 'lettuce'
    ])
    expected = (('2017/11', '2017/12', '2018/01'), None)
    actual = grid.get_period_names(args, tuple(ledger_args), 'month')
    assert actual == expected
    mock_ledger_output.assert_called_once_with(
        ('register', '--begin', 'banana', '--end', 'eggplant',
         '--period', 'pear', '--monthly', '--date-format', '%Y/%m',
         '--collapse', '--empty', 'lettuce')
    )


@mock.patch(__name__ + '.grid.date')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months_with_current(mock_ledger_output, mock_date):
    mock_date.today.return_value = date(2017, 12, 15)
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

                                <Total>                  0         0
        2018/01 - 2018/01       <Total>                  0         0''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args([
        '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', 'lettuce', '--current'
    ])
    expected = (('2017/11', '2017/12'), '2017/12')
    actual = grid.get_period_names(args, tuple(ledger_args), 'month')
    assert actual == expected
    mock_ledger_output.assert_called_once_with(
        ('register', '--begin', 'banana', '--end', 'eggplant',
         '--period', 'pear', '--monthly', '--date-format', '%Y/%m',
         '--collapse', '--empty', 'lettuce')
    )


@mock.patch(__name__ + '.grid.date')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_period_names_months_with_current_not_found(mock_ledger_output,
                                                        mock_date):
    mock_date.today.return_value = date(2019, 12, 15)
    output = dedent('''\
        2017/11 - 2017/11       <Total>                  0         0
        2017/12 - 2017/12       <Total>                  0         0

        2018/01 - 2018/01       <Total>                  0         0''')
    mock_ledger_output.return_value = output
    args, ledger_args = grid.get_args([
        '--begin', 'banana', '--end', 'eggplant',
        '--period', 'pear', 'lettuce', '--current'
    ])
    expected = (('2017/11', '2017/12', '2018/01'), None)
    actual = grid.get_period_names(args, tuple(ledger_args), 'month')
    assert actual == expected
    mock_ledger_output.assert_called_once_with(
        ('register', '--begin', 'banana', '--end', 'eggplant',
         '--period', 'pear', '--monthly', '--date-format', '%Y/%m',
         '--collapse', '--empty', 'lettuce')
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts(mock_ledger_output):
    output = dedent('''\
                     $ 17.37  expenses: car: gas
                      $ 6.50  expenses: car: maintenance
                  $ 1,001.78  expenses: widgets
        --------------------
                  $ 1,025.65''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
        'expenses: car: maintenance': 6.50,
        'expenses: widgets': 1001.78,
    }
    assert grid.get_column_accounts('2018', tuple()) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_depth_one(mock_ledger_output):
    output = dedent('''\
                     $ 10.00  apple: banana: cantaloupe
                     $ 20.00  apple: banana: eggplant
                     $ 40.00  grape: kiwi
                     $ 80.00  grape: fig
        --------------------
                    $ 150.00''')
    mock_ledger_output.return_value = output
    expected = {
        'apple': 30,
        'grape': 120,
    }
    assert grid.get_column_accounts('2018', tuple(), depth=1) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_depth_two(mock_ledger_output):
    output = dedent('''\
                     $ 10.00  apple: banana: cantaloupe
                     $ 20.00  apple: banana: eggplant
                     $ 40.00  grape:kiwi
                     $ 80.00  grape:fig
        --------------------
                    $ 150.00''')
    mock_ledger_output.return_value = output
    expected = {
        'apple: banana': 30,
        'grape:kiwi': 40,
        'grape:fig': 80,
    }
    assert grid.get_column_accounts('2018', tuple(), depth=2) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )


@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_differing_totals(mock_ledger_output, mock_print):
    output = dedent('''\
                    $ 49.998  expenses: parent
                    $ 29.999  expenses: parent: child
        --------------------
                    $ 49.998''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: parent': 49.998,
        'expenses: parent: child': 29.999,
    }
    assert grid.get_column_accounts('2018', tuple()) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )
    message = (
        "Warning: Differing total found between ledger's 49.998 and "
        "ledgerbil's 79.997 for --period 2018. Ledger's will be the correct "
        "total. This is mostly likely caused by funds being applied to both a "
        "parent and child account."
    )
    mock_print.assert_called_once_with(message, file=sys.stderr)


@pytest.mark.parametrize('test_input', [-2.5, 2.5251, 2.4749])
@mock.patch(__name__ + '.grid.sum')
@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_floating_point_diffs_not_ok(mock_ledger_output,
                                                         mock_print,
                                                         mock_sum,
                                                         test_input):
    """should warn about rounded total difference greater than .02"""
    output = dedent('''\
                      $ 1.25  expenses: car: gas
                      $ 1.25  expenses: car: maintenance
        --------------------
                      $ 2.50''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 1.25,
        'expenses: car: maintenance': 1.25,
    }
    mock_sum.return_value = test_input
    assert grid.get_column_accounts('2018', tuple()) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )
    message = (
        "Warning: Differing total found between ledger's 2.5 and "
        f"ledgerbil's {test_input} for --period 2018. Ledger's will be "
        "the correct total. This is mostly likely caused by funds being "
        "applied to both a parent and child account."
    )
    mock_print.assert_called_once_with(message, file=sys.stderr)


@pytest.mark.parametrize('test_input', [2.52, 2.525, 2.5, 2.48, 2.475])
@mock.patch(__name__ + '.grid.sum')
@mock.patch(__name__ + '.grid.warn_column_total')
@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_floating_point_diffs_ok(mock_ledger_output,
                                                     mock_warn,
                                                     mock_sum,
                                                     test_input):
    """should not warn about rounded total diff less than or equal to .02"""
    # within a penny seems close enough
    output = dedent('''\
                      $ 1.25  expenses: car: gas
                      $ 1.25  expenses: car: maintenance
        --------------------
                      $ 2.50''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 1.25,
        'expenses: car: maintenance': 1.25,
    }
    mock_sum.return_value = test_input
    assert grid.get_column_accounts('2018', tuple()) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )
    mock_warn.assert_not_called()


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_no_total(mock_ledger_output):
    output = dedent('''\
                     $ 17.37  expenses: car: gas''')
    mock_ledger_output.return_value = output
    expected = {
        'expenses: car: gas': 17.37,
    }
    assert grid.get_column_accounts('2018', tuple()) == expected
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_accounts_no_values(mock_ledger_output):
    output = ''
    mock_ledger_output.return_value = output
    assert grid.get_column_accounts('2018', tuple()) == {}
    mock_ledger_output.assert_called_once_with(
        ('balance', '--flat', '--period', '2018')
    )


@mock.patch(__name__ + '.grid.get_ledger_output')
def test_get_column_payees(mock_ledger_output):
    output = dedent('''\
        food and stuff
        17-Nov-01 - 18-Jan-05    <Total>      $ 102.03           $ 102.03

        gas n go
        18-Jan-03 - 18-Jan-03    <Total>        $23.87             $23.87

        johnny paycheck
        17-Nov-15 - 17-Nov-30    <Total>    $ 1,381.32         $ 1,381.32

        jurassic fork
        18-Jan-08 - 18-Jan-08    <Total>       $ 42.17            $ 42.17''')
    mock_ledger_output.return_value = output
    expected = {
        'food and stuff': 102.03,
        'gas n go': 23.87,
        'johnny paycheck': 1381.32,
        'jurassic fork': 42.17
    }
    assert grid.get_column_payees('blah', ('bogus', )) == expected
    mock_ledger_output.assert_called_once_with(
        ('register', 'expenses', '--group-by', '(payee)', '--collapse',
         '--subtotal', '--depth', '1', '--period', 'blah', 'bogus')
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
        ('bratwurst', 'knockwurst'),
        ('?', '!'),
        payees=True
    )
    assert payees == expected_payees
    assert columns == expected_columns
    mock_get_column_payees.assert_has_calls([
        mock.call('bratwurst', ('?', '!')),
        mock.call('knockwurst', ('?', '!')),
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

    accounts, columns = grid.get_columns(('lemon', 'lime'), tuple('salt!'))
    assert accounts == expected_accounts
    assert columns == expected_columns
    mock_get_column_accounts.assert_has_calls([
        mock.call('lemon', tuple('salt!'), 0),
        mock.call('lime', tuple('salt!'), 0),
    ])


@mock.patch(__name__ + '.grid.get_column_accounts')
def test_get_columns_with_current(mock_get_column_accounts):
    lemon_column = {'expenses: widgets': 1001.78}
    lime_column = {'expenses: unicorns': -10123.55}
    mock_get_column_accounts.side_effect = [lemon_column, lime_column]

    expected_columns = {'lemon': lemon_column, 'lime': lime_column}
    expected_accounts = {'expenses: unicorns', 'expenses: widgets'}

    accounts, columns = grid.get_columns(
        ('lemon', 'lime'),
        ('salt!', ),
        current='lime'
    )
    assert accounts == expected_accounts
    assert columns == expected_columns
    mock_get_column_accounts.assert_has_calls([
        mock.call('lemon', ('salt!', ), 0),
        mock.call('lime', ('salt!', '--end', 'tomorrow'), 0),
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
    ['lemon', 'lime', grid.TOTAL_HEADER, grid.EMPTY_VALUE],
    [90, 50, 140, 'expenses: widgets'],
    [100, 10, 110, 'expenses: car: gas'],
    [0, 20, 20, 'expenses: unicorns'],
    [-50, 0, -50, 'expenses: car: maintenance'],
    [140, 80, 220, grid.TOTAL_HEADER],
]

expected_sort_rows_by_row_header = [
    ['lemon', 'lime', grid.TOTAL_HEADER, grid.EMPTY_VALUE],
    [100, 10, 110, 'expenses: car: gas'],
    [-50, 0, -50, 'expenses: car: maintenance'],
    [0, 20, 20, 'expenses: unicorns'],
    [90, 50, 140, 'expenses: widgets'],
    [140, 80, 220, grid.TOTAL_HEADER],
]

expected_sort_rows_by_column_header = [
    ['lemon', 'lime', grid.TOTAL_HEADER, grid.EMPTY_VALUE],
    [90, 50, 140, 'expenses: widgets'],
    [0, 20, 20, 'expenses: unicorns'],
    [100, 10, 110, 'expenses: car: gas'],
    [-50, 0, -50, 'expenses: car: maintenance'],
    [140, 80, 220, grid.TOTAL_HEADER],
]

expected_sort_rows_by_total_with_limit = [
    ['lemon', 'lime', grid.TOTAL_HEADER, grid.EMPTY_VALUE],
    [90, 50, 140, 'expenses: widgets'],
    [100, 10, 110, 'expenses: car: gas'],
    [190, 60, 250, grid.TOTAL_HEADER],
]


expected_rows_total_only = [
    [grid.TOTAL_HEADER, grid.EMPTY_VALUE],
    [110, 'expenses: car: gas'],
    [-50, 'expenses: car: maintenance'],
    [20, 'expenses: unicorns'],
    [140, 'expenses: widgets'],
    [220, grid.TOTAL_HEADER],
]


@pytest.mark.parametrize('test_input, expected', [
    ((grid.SORT_DEFAULT, 0, False), expected_sort_rows_by_total),
    (('unrecognized', 0, False), expected_sort_rows_by_total),
    (('row', 0, False), expected_sort_rows_by_row_header),
    (('lime', 0, False), expected_sort_rows_by_column_header),
    ((grid.SORT_DEFAULT, 2, False), expected_sort_rows_by_total_with_limit),
    (('row', 0, True), expected_rows_total_only),
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
    columns = None  # only needed by get_grid which is mocked
    period_names = ('lemon', 'lime')
    sort, limit, total_only = test_input
    actual = grid.get_rows(
        row_headers,
        columns,
        period_names,
        sort,
        limit,
        total_only
    )
    assert actual == expected


@mock.patch(__name__ + '.grid.get_grid')
def test_get_rows_single_column(mock_get_grid):
    mock_get_grid.return_value = {
        'expenses: car: gas': {'lemon': 100},
        'expenses: car: maintenance': {'lemon': 120},
    }
    row_headers = {
        'expenses: car: gas',
        'expenses: car: maintenance',
    }
    columns = None  # only needed by get_grid which is mocked
    period_names = ('lemon',)
    actual = grid.get_rows(row_headers, columns, period_names)
    expected = [
        ['lemon', grid.EMPTY_VALUE],
        [120, 'expenses: car: maintenance'],
        [100, 'expenses: car: gas'],
        [220, grid.TOTAL_HEADER],
    ]
    assert actual == expected


@mock.patch(__name__ + '.grid.get_grid')
def test_get_rows_single_row(mock_get_grid):
    mock_get_grid.return_value = {
        'expenses: car: gas': {'lemon': 100, 'lime': 10},
    }
    row_headers = {
        'expenses: car: gas',
    }
    columns = None  # only needed by get_grid which is mocked
    period_names = ('lemon', 'lime')
    actual = grid.get_rows(row_headers, columns, period_names)
    expected = [
        ['lemon', 'lime', grid.TOTAL_HEADER, grid.EMPTY_VALUE],
        [100, 10, 110, 'expenses: car: gas'],
    ]
    assert actual == expected


@mock.patch(__name__ + '.grid.get_grid')
def test_get_rows_single_row_and_column(mock_get_grid):
    mock_get_grid.return_value = {
        'expenses: car: gas': {'lemon': 100},
    }
    row_headers = {
        'expenses: car: gas',
    }
    columns = None  # only needed by get_grid which is mocked
    period_names = ('lemon',)
    actual = grid.get_rows(row_headers, columns, period_names)
    expected = [
        ['lemon', grid.EMPTY_VALUE],
        [100, 'expenses: car: gas'],
    ]
    assert actual == expected


def test_get_csv_report():
    """csv report should turn whatever it's given into csv"""
    rows = [
        [1, 2, 3, 4, 5],
        ['a', 'b', '"c"', 'd e f', 'g, h'],
        ['', 4, '', 6, 'glurg'],
    ]
    expected = dedent(f'''\
        1,2,3,4,5
        a,b,"""c""",d e f,"g, h"
        ,4,,6,glurg
        ''')
    cvs_report = grid.get_csv_report(rows)
    assert cvs_report == expected


def test_get_flat_report():
    rows = [
        ['lemon', 'lime', grid.TOTAL_HEADER, ''],
        [2.65, 500.1, 502.75, 'expenses: widgets'],
        [17.37, 28.19, 45.56, 'expenses: car: gas'],
        [6.5, 0, 6.5, 'expenses: car: maintenance'],
        [0, -10123.55, -10123.55, 'expenses: unicorns'],
        [26.52, -9595.26, -9568.74, grid.EMPTY_VALUE],
    ]
    report = grid.get_flat_report(rows)
    helper = OutputFileTester(f'test_grid_flat_report')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_flat_report_single_column():
    """The flat report should handle rows without a total column"""
    rows = [
        ['lemon', ''],
        [2.65, 'expenses: widgets'],
        [17.37, 'expenses: car: gas'],
        [6.5, 'expenses: car: maintenance'],
        [8, 'expenses: unicorns'],
        [34.52, grid.TOTAL_HEADER],
    ]
    report = grid.get_flat_report(rows)
    expected = (
        '         lemon\n'
        '        $ 2.65  expenses: widgets\n'
        '       $ 17.37  expenses: car: gas\n'
        '        $ 6.50  expenses: car: maintenance\n'
        '        $ 8.00  expenses: unicorns\n'
        '  ------------\n'
        '       $ 34.52\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_flat_report_single_row():
    """The total row and column should be omitted if only one data point"""
    rows = [
        ['lemon', 'lime', grid.TOTAL_HEADER, ''],
        [2.65, 500.1, 502.75, 'expenses: widgets'],
        [2.65, 500.1, 502.75, grid.EMPTY_VALUE],
    ]
    report = grid.get_flat_report(rows)
    expected = (
        '         lemon          lime         Total\n'
        '        $ 2.65      $ 500.10      $ 502.75  expenses: widgets\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_flat_report_single_row_and_column():
    """The total row (and dashes) should be omitted if only one data row"""
    rows = [
        ['lemon', ''],
        [2.65, 'expenses: widgets'],
        [2.65, grid.EMPTY_VALUE],
    ]
    report = grid.get_flat_report(rows)
    expected = (
        '         lemon\n'
        '        $ 2.65  expenses: widgets\n'
    )
    assert Colorable.get_plain_string(report) == expected


@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_month(mock_pnames, mock_cols, mock_rows, mock_report):
    period_names, row_headers, columns, rows, flat_report = (
        ('garlic', 'paprika'), 'fennel', 'tarragon', ['basil'], 'parsley',
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
        row_headers, columns, period_names, grid.SORT_DEFAULT, 0, False
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
        ('paprika', 'garlic'), 'fennel', 'tarragon', 'parsley',
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
        row_headers, columns, period_names, 'cloves', 20, False
    )


@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_flat_transposed(mock_pnames, mock_cols,
                                         mock_rows, mock_report):
    period_names, row_headers, columns = (
        ('garlic', 'paprika'), set('fennel'), 'tarragon',
    )
    rows = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    mock_rows.return_value = rows
    mock_pnames.return_value = (period_names, None)
    mock_cols.return_value = (row_headers, columns)

    args, ledger_args = grid.get_args(['--transpose'])
    grid.get_grid_report(args, ledger_args)

    expected_rows = [
        [6, 9, 3],
        [4, 7, 1],
        [5, 8, 2],
    ]
    mock_report.assert_called_once_with(expected_rows)


@mock.patch(__name__ + '.grid.get_csv_report')
@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_csv(mock_pnames, mock_cols, mock_rows,
                             mock_flat_report, mock_csv_report):
    rows = [
        [1, 2, 3],
        ['a', 'b', 'c'],
        [4, '', 6],
    ]
    mock_pnames.return_value = ('ra', 'dar')
    mock_cols.return_value = ('fu', 'bar')
    mock_rows.return_value = rows
    mock_csv_report.return_value = 'csv,report\n'

    args, ledger_args = grid.get_args(['--csv'])
    grid_report_output = grid.get_grid_report(args, ledger_args)

    expected_rows = [
        [3, 1, 2],
        ['c', 'a', 'b'],
        [6, 4, ''],
    ]
    mock_csv_report.assert_called_once_with(expected_rows)
    assert grid_report_output == 'csv,report\n'
    assert not mock_flat_report.called


@mock.patch(__name__ + '.grid.get_csv_report')
@mock.patch(__name__ + '.grid.get_flat_report')
@mock.patch(__name__ + '.grid.get_rows')
@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_csv_transposed(mock_pnames, mock_cols, mock_rows,
                                        mock_flat_report, mock_csv_report):
    rows = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]
    mock_pnames.return_value = ('ra', 'dar')
    mock_cols.return_value = ('fu', 'bar')
    mock_rows.return_value = rows
    mock_csv_report.return_value = 'csv,report\n'

    args, ledger_args = grid.get_args(['--csv', '--transpose'])
    grid_report_output = grid.get_grid_report(args, ledger_args)

    expected_rows = [
        [3, 6, 9],
        [1, 4, 7],
        [2, 5, 8],
    ]
    mock_csv_report.assert_called_once_with(expected_rows)
    assert grid_report_output == 'csv,report\n'
    assert not mock_flat_report.called


@mock.patch(__name__ + '.grid.get_ledger_output', return_value='')
def test_get_grid_report_no_period_names(mock_ledger_output):
    # no results from initial ledger query for periods
    args, ledger_args = grid.get_args([])
    assert grid.get_grid_report(args, tuple(ledger_args)) == ''


@mock.patch(__name__ + '.grid.get_columns')
@mock.patch(__name__ + '.grid.get_period_names')
def test_get_grid_report_no_results(mock_pnames, mock_cols):
    period_names, row_headers, columns = (
        ('paprika', 'garlic'), set(), 'tarragon',
    )

    mock_pnames.return_value = (period_names, 'celery')
    mock_cols.return_value = (row_headers, columns)

    args, ledger_args = grid.get_args([])
    assert grid.get_grid_report(args, ledger_args) == ''


@pytest.mark.parametrize('test_input, expected', [
    ((['2017'], 14), '          2017'),
    ((['2017'], 20), '                2017'),
    ((['abc', 'xyz'], 5), '  abc  xyz'),
    ((['a b c', 'x & z'], 6), ' a b c x & z'),
    ((['a:b:c:d', 'l:m:n:o:p'], 12), '     a:b:c:d   l:m:n:o:p'),
    ((['abc: xyz', '123: 456'], 10), '  abc: xyz  123: 456'),
    ((['a', 'b', 'c'], 3), '  a  b  c'),
    ((['a', 'b', 'c', 'd', 'ef'], 4), '   a   b   c   d  ef'),
    ((['Assets: Bob'], 12), '     Assets:\n         Bob'),
    ((['a:b:c', 'x:y'], 3), ' a:   \n b: x:\n  c  y'),
])
def test_get_flat_report_header(test_input, expected):
    assert grid.get_flat_report_header(*test_input) == f"{expected}\n"


@pytest.mark.parametrize('test_input, expected', [
    (([''], 5), [['']]),  # one header with one item
    ((['', ''], 5), [[''], ['']]),  # two headers with one item each
    ((['abc'], 5), [['abc']]),
    ((['abc: xyz'], 10), [['abc: xyz']]),
    ((['abc:xyz'], 10), [['abc:xyz']]),
    ((['abc:xyz'], 5), [['abc:', 'xyz']]),
    ((['abcd:xyz'], 5), [['abc~', 'xyz']]),
    ((['Assets: Bob'], 20), [['Assets:', 'Bob']]),
    ((['Assets:Bob'], 20), [['Assets:', 'Bob']]),
    ((['Assets Bob'], 20), [['Assets Bob']]),
    ((['LIABILITIES: BOB'], 20), [['LIABILITIES:', 'BOB']]),
    ((['income: bob'], 20), [['income:', 'bob']]),
    ((['expenses: bob'], 20), [['expenses:', 'bob']]),
    ((['equity: bob'], 20), [['equity:', 'bob']]),
    ((['abc: xyz: 1234: 1234'], 5), [['abc:', 'xyz:', '123~', '1234']]),
    ((['expenses: abc'], 5), [['exp~', 'abc']]),
    ((['expenses: fu bar: scoob'], 16), [['expenses:', 'fu bar: scoob']]),
    ((['expenses: fu: bar scooby'], 16), [['expenses:', 'fu: bar', 'scooby']]),
    ((['crate & barrel'], 14), [['crate &', 'barrel']]),
    ((['struncated & white'], 8), [['strunc~', '& white']]),
    ((['white & struncated'], 8), [['white &', 'strunc~']]),
    ((['2017', '2018'], 14), [['2017'], ['2018']]),
    ((['2017', '2018', 'Total'], 14), [['2017'], ['2018'], ['Total']]),
    ((['2017/01', '2017/02'], 14), [['2017/01'], ['2017/02']]),
    ((['abc: xyz', 'def: lmn'], 5), [['abc:', 'xyz'], ['def:', 'lmn']]),
    ((['a', 'a: b'], 3), [['', 'a'], ['a:', 'b']]),
    (
        (['a', 'a b', 'a b c'], 2),
        [['', '', 'a'], ['', 'a', 'b'], ['a', 'b', 'c']]
    ),
    ((['investments'], 14), [['investments']]),
    ((['investmentsx'], 14), [['investment~']]),
])
def test_get_flat_report_header_lists(test_input, expected):
    assert grid.get_flat_report_header_lists(*test_input) == expected


@mock.patch(__name__ + '.grid.print')
@mock.patch(__name__ + '.grid.get_grid_report')
def test_main(mock_get_grid_report, mock_print):
    mock_get_grid_report.return_value = 'bananas!'
    args, unknown = grid.get_args(['-y', 'xyz'])
    grid.main(['-y', 'xyz'])
    mock_get_grid_report.assert_called_once_with(args, ('xyz', ))
    mock_print.assert_called_once_with('bananas!', end='')


@pytest.mark.parametrize('test_input, expected', [
    (['-y'], True),
    (['--year'], True),
    ([], True),
])
def test_args_year(test_input, expected):
    args, ledger_args = grid.get_args(test_input)
    assert args.year is expected
    assert ledger_args == []


@pytest.mark.parametrize('test_input, expected', [
    (['-m'], True),
    (['--month'], True),
    ([], False),
])
def test_args_month(test_input, expected):
    args, ledger_args = grid.get_args(test_input)
    assert args.month is expected
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
    assert args.payees is expected


@pytest.mark.parametrize('test_input, expected', [
    (['--current'], True),
    ([], False),
])
def test_args_current(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.current is expected


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
    _, ledger_args = grid.get_args(test_input)
    assert ledger_args == expected


@pytest.mark.parametrize('test_input, expected', [
    (['--csv'], True),
    ([], False),
])
def test_args_csv(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.csv is expected


@pytest.mark.parametrize('test_input, expected', [
    (['-t'], True),
    (['--transpose'], True),
    ([], False),
])
def test_args_transpose(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.transpose is expected


@pytest.mark.parametrize('test_input, expected', [
    (['-T'], True),
    (['--total-only'], True),
    ([], False),
])
def test_args_total_only(test_input, expected):
    args, _ = grid.get_args(test_input)
    assert args.total_only is expected
