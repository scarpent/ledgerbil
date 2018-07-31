from .. import grid, runner
from ...tests.filetester import FileTester
from ...tests.helpers import OutputFileTester


class MockSettings:
    LEDGER_COMMAND = ('ledger', )
    LEDGER_DIR = FileTester.testdir
    LEDGER_FILES = ['grid-end-to-end.ldg']


def setup_function(module):
    runner.settings = MockSettings()


def test_get_grid_report_flat_report_expenses():
    args, ledger_args = grid.get_args(['expenses', '--sort', 'row'])
    report = grid.get_grid_report(args, tuple(ledger_args))
    helper = OutputFileTester(f'test_grid_end_to_end_flat_expenses')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_flat_report_expenses_monthly():
    args, ledger_args = grid.get_args(['expenses', '--sort', 'row', '--month'])
    report = grid.get_grid_report(args, tuple(ledger_args))
    helper = OutputFileTester(f'test_grid_end_to_end_flat_monthly_expenses')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_flat_report_payees():
    args, ledger_args = grid.get_args(['--payees'])
    report = grid.get_grid_report(args, tuple(ledger_args))
    helper = OutputFileTester(f'test_grid_end_to_end_flat_payees')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()


def test_get_grid_report_csv_report_all():
    args, ledger_args = grid.get_args(['--csv'])
    report = grid.get_grid_report(args, tuple(ledger_args))
    helper = OutputFileTester(f'test_grid_end_to_end_csv_all')
    helper.save_out_file(report)
    helper.assert_out_equals_expected()
