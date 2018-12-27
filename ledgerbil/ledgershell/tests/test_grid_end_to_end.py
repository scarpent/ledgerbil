from textwrap import dedent

from .. import grid
from ... import settings, settings_getter
from ...colorable import Colorable
from ...tests import filetester as FT
from ...tests.helpers import OutputFileTester

# These tests actually run ledger for a bit of integration testing.
# We'll try to make sure test_grid.py continues to test 100% of grid.py.


class MockSettings:
    LEDGER_COMMAND = ('ledger', )
    LEDGER_DIR = FT.testdir
    LEDGER_FILES = ['grid-end-to-end.ldg']
    NETWORTH_ACCOUNTS = settings_getter.defaults['NETWORTH_ACCOUNTS']
    DATE_FORMAT_MONTH = settings_getter.defaults['DATE_FORMAT_MONTH']


class MockSettingsAltDateFormat(MockSettings):
    DATE_FORMAT_MONTH = '%Y-%m'


def setup_module():
    settings_getter.settings = MockSettings()


def teardown_module():
    settings_getter.settings = settings.Settings()


def test_get_grid_report_flat_report_expenses():
    args, ledger_args = grid.get_args(['expenses', '--sort', 'row'])
    report = grid.get_grid_report(args, ledger_args)
    helper = OutputFileTester(f'test_grid_end_to_end_flat_expenses')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_flat_report_transposed():
    args, ledger_args = grid.get_args(['food', '--transpose'])
    report = grid.get_grid_report(args, ledger_args)
    helper = OutputFileTester(f'test_grid_end_to_end_flat_transposed')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_flat_report_expenses_monthly():
    args, ledger_args = grid.get_args(['expenses', '--sort', 'row', '--month'])
    report = grid.get_grid_report(args, ledger_args)
    helper = OutputFileTester(f'test_grid_end_to_end_flat_monthly_expenses')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_flat_report_single_column():
    args, ledger_args = grid.get_args(['food', '--period', '2018'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '          2018\n'
        '       $ 57.40  expenses: food: groceries\n'
        '       $ 42.17  expenses: food: dining out\n'
        '  ------------\n'
        '       $ 99.57\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_flat_report_single_column_transposed():
    args, ledger_args = grid.get_args(
        ['food', '--period', '2018', '--transpose']
    )
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '     expenses:     expenses:              \n'
        '         food:         food:              \n'
        '     groceries    dining out         Total\n'
        '       $ 57.40       $ 42.17       $ 99.57  2018\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_flat_report_single_row():
    args, ledger_args = grid.get_args(['groceries'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '          2017          2018         Total\n'
        '       $ 34.63       $ 57.40       $ 92.03  expenses: food: groceries'
        '\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_flat_report_single_row_transposed():
    args, ledger_args = grid.get_args(['groceries', '--transpose'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '     expenses:\n'
        '         food:\n'
        '     groceries\n'
        '       $ 34.63  2017\n'
        '       $ 57.40  2018\n'
        '  ------------\n'
        '       $ 92.03\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_flat_report_single_row_and_column():
    args, ledger_args = grid.get_args(['groceries', '--period', '2018'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '          2018\n'
        '       $ 57.40  expenses: food: groceries\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_flat_report_payees():
    args, ledger_args = grid.get_args(['--payees', 'expenses'])
    report = grid.get_grid_report(args, ledger_args)
    helper = OutputFileTester(f'test_grid_end_to_end_flat_payees')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_csv_report_all():
    args, ledger_args = grid.get_args(['--csv'])
    report = grid.get_grid_report(args, ledger_args)
    helper = OutputFileTester(f'test_grid_end_to_end_csv_all')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_csv_report_transposed():
    args, ledger_args = grid.get_args(['--csv', '--transpose', 'food'])
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,expenses: food: groceries,expenses: food: dining out,Total
        2017,34.63,0,34.63
        2018,57.4,42.17,99.57
        Total,92.03,42.17,134.2
    ''')
    assert report == expected


def test_get_grid_report_csv_report_single_column():
    args, ledger_args = grid.get_args(['--csv', '--period', '2018', 'food'])
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,2018
        expenses: food: groceries,57.4
        expenses: food: dining out,42.17
        Total,99.57
    ''')
    assert report == expected


def test_get_grid_report_csv_report_single_column_transposed_to_single_row():
    args, ledger_args = grid.get_args(
        ['--csv', '--period', '2018', 'food', '--transpose']
    )
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,expenses: food: groceries,expenses: food: dining out,Total
        2018,57.4,42.17,99.57
    ''')
    assert report == expected


def test_get_grid_report_csv_report_single_row():
    args, ledger_args = grid.get_args(['--csv', 'groceries'])
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,2017,2018,Total
        expenses: food: groceries,34.63,57.4,92.03
    ''')
    assert report == expected


def test_get_grid_report_csv_report_single_row_transposed_to_single_column():
    args, ledger_args = grid.get_args(['--csv', 'groceries', '--transpose'])
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,expenses: food: groceries
        2017,34.63
        2018,57.4
        Total,92.03
    ''')
    assert report == expected


def test_get_grid_report_csv_report_single_row_and_column():
    args, ledger_args = grid.get_args(
        ['--csv', 'groceries', '--period', '2018']
    )
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,2018
        expenses: food: groceries,57.4
    ''')
    assert report == expected


def test_get_grid_report_csv_report_single_row_and_column_transposed():
    args, ledger_args = grid.get_args(
        ['--csv', 'groceries', '--period', '2018', '--transpose']
    )
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,expenses: food: groceries
        2018,57.4
    ''')
    assert report == expected


def test_get_grid_report_csv_total_only():
    args, ledger_args = grid.get_args(['--csv', 'food', '--total-only'])
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,Total
        expenses: food: groceries,92.03
        expenses: food: dining out,42.17
        Total,134.2
    ''')
    assert report == expected


def test_get_grid_report_csv_total_only_transposed():
    args, ledger_args = grid.get_args(
        ['--csv', 'food', '--total-only', '--transpose']
    )
    report = grid.get_grid_report(args, ledger_args)
    expected = dedent('''\
        ,expenses: food: groceries,expenses: food: dining out,Total
        Total,92.03,42.17,134.2
    ''')
    assert report == expected


def test_get_grid_report_networth_flat_report():
    args, ledger_args = grid.get_args(['--net-worth'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '          2017          2018\n'
        '    $ 1,427.71    $ 1,304.27  net worth\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_networth_flat_report_transposed():
    args, ledger_args = grid.get_args(['--net-worth', '--transpose'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '     net worth\n'
        '    $ 1,427.71  2017\n'
        '    $ 1,304.27  2018\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_networth_flat_report_different_date_format():
    settings_getter.settings = MockSettingsAltDateFormat()
    args, ledger_args = grid.get_args(
        ['--net-worth', '--month', '--transpose', '--period', '2017']
    )
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        '     net worth\n'
        '    $ 1,439.47  2017-11\n'
        '    $ 1,427.71  2017-12\n'
    )
    assert Colorable.get_plain_string(report) == expected


def test_get_grid_report_networth_csv():
    args, ledger_args = grid.get_args(['--net-worth', '--csv'])
    report = grid.get_grid_report(args, ledger_args)
    expected = (
        ',2017,2018\n'
        '    $ 1,427.71    $ 1,304.27  net worth\n'
    )
    expected = dedent('''\
        ,2017,2018
        net worth,1427.71,1304.27
    ''')
    assert Colorable.get_plain_string(report) == expected
