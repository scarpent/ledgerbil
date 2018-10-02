import os
from datetime import date
from textwrap import dedent
from unittest import TestCase, mock

import pytest
from dateutil.relativedelta import relativedelta

from .filetester import FileTester as FT
from .helpers import Redirector
from .test_schedulefile import schedule_testdata

from .. import (  # noqa (reconciler and scheduler used in patches) isort:skip
    ledgerbil, reconciler, scheduler, settings, settings_getter, util
)


class MainBasicInput(TestCase):

    def test_main_no_options_on_sorted_file(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.read_file(FT.alpha_sortedfile)
        tempfile = FT.copy_to_temp_file(FT.alpha_sortedfile)
        ledgerbil.main(['--file', tempfile])
        actual = FT.read_file(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)

    def test_main_no_options_on_unsorted_file(self):
        """main should parse and write unsorted file unchanged"""
        expected = FT.read_file(FT.alpha_unsortedfile)
        tempfile = FT.copy_to_temp_file(FT.alpha_unsortedfile)
        ledgerbil.main(['--file', tempfile])
        actual = FT.read_file(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)


class Sorting(TestCase):

    def test_main_sort_on_sorted_file(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.read_file(FT.alpha_sortedfile)
        tempfile = FT.copy_to_temp_file(FT.alpha_sortedfile)
        ledgerbil.main(['--file', tempfile, '--sort'])
        actual = FT.read_file(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)

    def test_main_sorted_no_options(self):
        """main should parse unsorted file and write sorted file"""
        expected = FT.read_file(FT.alpha_sortedfile)
        tempfile = FT.copy_to_temp_file(FT.alpha_unsortedfile)
        ledgerbil.main(['--file', tempfile, '--sort'])
        actual = FT.read_file(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)


def test_main_sort_different_date_format():
    """main should fail to sort file if date format is different
       than in ledger entries"""
    class MockSettings:
        DATE_FORMAT = '%Y-%m-%d'
    settings_getter.settings = MockSettings()
    expected = FT.read_file(FT.alpha_unsortedfile)
    tempfile = FT.copy_to_temp_file(FT.alpha_unsortedfile)
    ledgerbil.main(['--file', tempfile, '--sort'])
    actual = FT.read_file(tempfile)
    os.remove(tempfile)
    assert actual == expected
    settings_getter.settings = settings.Settings()


@mock.patch(__name__ + '.ledgerbil.LedgerFile.write_file')
@mock.patch(__name__ + '.ledgerbil.LedgerFile.sort')
@mock.patch(__name__ + '.ledgerbil.LedgerFile.__init__')
def test_sorting_multiple_files(mock_init, mock_sort, mock_write_file):
    mock_init.return_value = None
    with FT.temp_input('; no data 1') as file1:
        with FT.temp_input('; no data 2') as file2:
            ledgerbil.main(['--file', file1, '--file', file2, '--sort'])

    assert mock_init.call_args_list == [
        mock.call(file1, None),
        mock.call(file2, None),
    ]
    # It would be nice to be able to further confirm that each instanace
    # of Ledgerfile called these methods
    assert mock_sort.call_args_list == [mock.call(), mock.call()]
    assert mock_write_file.call_args_list == [mock.call(), mock.call()]


class MainErrors(Redirector):

    def test_main_next_scheduled_date(self):
        ledgerbil.main(['-n'])
        self.assertEqual(
            'error: -s/--schedule is required',
            self.redirecterr.getvalue().strip()
        )

    def test_main_file_required(self):
        ledgerbil.main([])
        self.assertEqual(
            'error: -f/--file is required',
            self.redirecterr.getvalue().strip()
        )


class Scheduler(Redirector):

    @staticmethod
    def get_schedule_file(the_date, schedule, enter_days=7):
        return (
            f';; scheduler ; enter {enter_days} days\n'
            '\n'
            f'{the_date} bananas unlimited\n'
            f'    ;; schedule ; {schedule}\n'
            '    e: misc\n'
            '    l: credit card                     $-50\n\n'
        )

    @staticmethod
    def get_ledger_file(the_date):
        return (
            f'{the_date} bananas unlimited\n'
            '    e: misc\n'
            '    l: credit card                     $-50\n\n'
        )

    def test_scheduler(self):
        lastmonth = date.today() - relativedelta(months=1)
        testdate = date(lastmonth.year, lastmonth.month, 15)
        schedule = 'monthly ;; every 2 months'

        schedulefiledata = self.get_schedule_file(
            util.get_date_string(testdate),
            schedule
        )
        tempschedulefile = FT.write_to_temp_file(
            FT.testdir + 'test_scheduler_schedule_file',
            schedulefiledata
        )

        templedgerfile = FT.write_to_temp_file(
            FT.testdir + 'test_scheduler_ledger_file',
            ''
        )

        ledgerbil.main([
            '--file', templedgerfile,
            '--schedule', tempschedulefile,
        ])

        schedulefile_actual = FT.read_file(tempschedulefile)
        schedulefile_expected = self.get_schedule_file(
            util.get_date_string(
                testdate + relativedelta(months=2)
            ),
            schedule
        )

        ledgerfile_actual = FT.read_file(templedgerfile)
        ledgerfile_expected = self.get_ledger_file(
            util.get_date_string(testdate)
        )

        os.remove(tempschedulefile)
        os.remove(templedgerfile)

        self.assertEqual(schedulefile_expected, schedulefile_actual)
        self.assertEqual(ledgerfile_expected, ledgerfile_actual)

    @mock.patch(__name__ + '.ledgerbil.LedgerFile')
    def test_next_scheduled_date(self, mock_ledgerfile):
        with FT.temp_input(schedule_testdata) as tempfile:
            ledgerbil.main(['-n', '-s', tempfile])
        assert self.redirect.getvalue().rstrip() == '2007/07/07'
        assert not mock_ledgerfile.called


@mock.patch(__name__ + '.ledgerbil.run_scheduler')
def test_scheduler_multiple_files(mock_scheduler):
    """The first ledger file should be used by the scheduler
       if more than one is passed in"""
    with FT.temp_input('; schedule file') as schedule_filename:
        with FT.temp_input('; ledger file') as ledger_filename:
            with FT.temp_input('; ledger file 2') as ledger2_filename:
                ledgerbil.main([
                    '--file', ledger_filename,
                    '--file', ledger2_filename,
                    '--schedule', schedule_filename
                ])

            mock_scheduler.assert_called_once()
            assert mock_scheduler.call_args[0][0].filename == ledger_filename
            assert mock_scheduler.call_args[0][1] == schedule_filename


@mock.patch(__name__ + '.ledgerbil.LedgerFile.sort')
@mock.patch(__name__ + '.ledgerbil.run_scheduler')
def test_scheduler_and_sort_can_be_called_together(mock_scheduler, mock_sort):
    mock_scheduler.return_value = None
    with FT.temp_input('; schedule file') as schedule_filename:
        with FT.temp_input('; ledger file') as ledger_filename:
            ledgerbil.main([
                '--file', ledger_filename,
                '--schedule', schedule_filename,
                '--sort'
            ])

    mock_scheduler.assert_called_once()
    mock_sort.assert_called_once()


@mock.patch(__name__ + '.ledgerbil.LedgerFile.sort')
@mock.patch(__name__ + '.ledgerbil.run_scheduler')
def test_scheduler_runs_before_sort(mock_scheduler, mock_sort):
    # By not setting a return_value for mock_scheduler, the return
    # value will be a mock which will appear as an error in the code
    # and cause a return before the sort is reached
    with FT.temp_input('; schedule file') as schedule_filename:
        with FT.temp_input('; ledger file') as ledger_filename:
            ledgerbil.main([
                '--file', ledger_filename,
                '--schedule', schedule_filename,
                '--sort'
            ])

    mock_scheduler.assert_called_once()
    assert not mock_sort.called


class ReconcilerTests(Redirector):

    def test_multiple_matches(self):
        # in different transactions
        ledgerbil.main([
            '--file', FT.test_rec_multiple_match,
            '--reconcile', 'checking'
        ])
        self.assertEqual(
            'More than one matching account:\n'
            '    a: checking down\n'
            '    a: checking up',
            self.redirecterr.getvalue().rstrip()
        )
        # in same transaction
        self.reset_err_redirect()
        ledgerbil.main([
            '--file', FT.test_rec_multiple_match,
            '--reconcile', 'cash'
        ])
        self.assertEqual(
            'More than one matching account:\n'
            '    a: cash in\n'
            '    a: cash out',
            self.redirecterr.getvalue().rstrip()
        )

    def test_multiple_statuses(self):
        ledgerbil.main([
            '--file', FT.test_rec_multiple_match,
            '--reconcile', 'mattress'
        ])
        self.assertEqual(
            'Unhandled multiple statuses: 2016/10/08 zillion',
            self.redirecterr.getvalue().rstrip()
        )

    def test_no_matching_account(self):
        result = ledgerbil.main([
            '--file', FT.test_reconcile,
            '--reconcile', 'schenectady schmectady'
        ])
        expected = 'No matching account found for "schenectady schmectady"'
        assert self.redirect.getvalue().rstrip() == expected
        assert result is None

    def test_no_matching_account_in_multiple(self):
        result = ledgerbil.main([
            '--file', FT.test_reconcile,
            '--file', FT.test_reconcile,
            '--reconcile', 'schenectady schmectady'
        ])
        expected = 'No matching account found for "schenectady schmectady"'
        assert self.redirect.getvalue().rstrip() == expected
        assert result is None


@mock.patch(__name__ + '.ledgerbil.LedgerFile.sort')
@mock.patch(__name__ + '.ledgerbil.run_scheduler')
@mock.patch(__name__ + '.ledgerbil.Ledgerbil.no_matching_account_found')
@mock.patch(__name__ + '.ledgerbil.run_reconciler')
def test_reconciler_takes_precedence_over_scheduler_and_sort(mock_reconciler,
                                                             mock_no_match,
                                                             mock_scheduler,
                                                             mock_sort):
    mock_scheduler.return_value = None
    mock_no_match.return_value = False
    with FT.temp_input('; schedule file') as schedule_filename:
        with FT.temp_input('; ledger file') as ledger_filename:
            ledgerbil.main([
                '--file', ledger_filename,
                '--schedule', schedule_filename,
                '--reconcile', 'abc',
                '--sort'
            ])

    mock_reconciler.assert_called_once()
    assert not mock_scheduler.called
    assert not mock_sort.called


@mock.patch(__name__ + '.ledgerbil.run_reconciler')
def test_run_reconciler_called(mock_run_reconciler):
    ledgerfile_data = dedent('''
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    ''')
    with FT.temp_input(ledgerfile_data) as tempfilename:
        ledgerbil.main(['--file', tempfilename, '--reconcile', 'bonds'])
    mock_run_reconciler.assert_called_once()


@mock.patch(__name__ + '.ledgerbil.LedgerFile')
@mock.patch(__name__ + '.ledgerbil.handle_error')
@mock.patch(__name__ + '.ledgerbil.reconciled_status')
def test_reconciled_status(mock_reconciled, mock_error, mock_ledgerfile):
    # reconciled status takes precedence over calling subsequent stuff
    ledgerbil.main(['--reconciled-status'])
    assert not mock_error.called
    assert not mock_ledgerfile.called
    mock_reconciled.assert_called_once_with()


@mock.patch(__name__ + '.reconciler.util.handle_error')
def test_reconciler_exception(mock_handle_error):
    ledgerfile_data = dedent('''
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    ''')
    with FT.temp_input(ledgerfile_data) as tempfilename:
        ledgerbil.main([
            '--file', tempfilename,
            '--reconcile', 'bonds'
        ])
    expected = 'Unhandled shares with non-shares: "a: 401k: bonds idx"'
    mock_handle_error.assert_called_once_with(expected)


def test_reconciler_exception_return_value():
    ledgerfile_data = dedent('''
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    ''')
    with FT.temp_input(ledgerfile_data) as tempfilename:
        return_value = ledgerbil.main([
            '--file', tempfilename,
            '--reconcile', 'bonds'
        ])
    assert return_value == -1


@mock.patch(__name__ + '.ledgerbil.handle_error')
def test_main_investments_with_argv_none(mock_handle_error):
    with mock.patch('sys.argv', ['/script']):
        ledgerbil.main()
    expected = 'error: -f/--file is required'
    mock_handle_error.assert_called_once_with(expected)


def test_main_investments_with_argv_none_retun_value():
    with mock.patch('sys.argv', ['/script']):
        assert ledgerbil.main() == -1


@mock.patch(__name__ + '.scheduler.handle_error')
def test_next_scheduled_date_scheduler_exception(mock_handle_error):
    schedulefile_data = ';; scheduler enter 567 days'
    with FT.temp_input(schedulefile_data) as tempfilename:
        ledgerbil.main(['--schedule', tempfilename, '-n'])
    expected = dedent('''\
            Invalid schedule file config:
            ;; scheduler enter 567 days
            Expected:
            ;; scheduler ; enter N days''')
    mock_handle_error.assert_called_once_with(expected)


def test_next_scheduled_date_scheduler_exception_return_value():
    schedulefile_data = ';; scheduler enter 567 days'
    with FT.temp_input(schedulefile_data) as tempfilename:
        assert ledgerbil.main(['--schedule', tempfilename, '-n']) == -1


@mock.patch(__name__ + '.scheduler.handle_error')
def test_scheduler_exception(mock_handle_error):
    with FT.temp_input(';; scheduler enter 321 days') as tempfilename:
        ledgerbil.main(
            ['--schedule', tempfilename, '-f', FT.testfile]
        )
    expected = dedent('''\
        Invalid schedule file config:
        ;; scheduler enter 321 days
        Expected:
        ;; scheduler ; enter N days''')
    mock_handle_error.assert_called_once_with(expected)


def test_scheduler_exception_return_value():
    with FT.temp_input(';; scheduler enter 321 days') as tempfilename:
        return_value = ledgerbil.main(
            ['--schedule', tempfilename, '-f', FT.testfile]
        )
    assert return_value == -1


@mock.patch(__name__ + '.ledgerbil.argparse.ArgumentParser.print_help')
def test_args_no_parameters(mock_print_help):
    ledgerbil.get_args([])
    mock_print_help.assert_called_once()


@pytest.mark.parametrize('test_input, expected', [
    ([], []),
    (['-f', 'bob'], ['bob']),
    (['--file', 'loblaw'], ['loblaw']),
    (['-f', 'bob', '-f', 'loblaw'], ['bob', 'loblaw']),
])
def test_args_file_option(test_input, expected):
    args = ledgerbil.get_args(test_input)
    assert args.file == expected


def test_args_file_option_and_filename_both_required():
    """should cause argparse error if file opt specified without file"""
    with pytest.raises(SystemExit) as excinfo:
        ledgerbil.get_args(['--file'])
    assert str(excinfo.value) == '2'


@pytest.mark.parametrize('test_input, expected', [
    ('-S', True),
    ('--sort', True),
    ('', False),
])
def test_args_sort_option(test_input, expected):
    options = ['-f', 'mario']
    if test_input:
        options.append(test_input)
    args = ledgerbil.get_args(options)
    assert args.sort is expected


@pytest.mark.parametrize('test_input, expected', [
    ('-s', 'robo'),
    ('--schedule', 'cop'),
])
def test_args_schedule_file_option(test_input, expected):
    args = ledgerbil.get_args([test_input, expected])
    assert args.schedule == expected


def test_args_schedule_filename_required_with_schedule_option():
    """argparse error if sched file opt specified without file"""
    with pytest.raises(SystemExit) as excinfo:
        ledgerbil.get_args(['--schedule'])
    assert str(excinfo.value) == '2'


@pytest.mark.parametrize('test_input, expected', [
    ('-n', True),
    ('--next-scheduled-date', True),
    ('', False),
])
def test_args_next_scheduled_date(test_input, expected):
    options = ['-f', 'gargle']
    if test_input:
        options.append(test_input)
    args = ledgerbil.get_args(options)
    assert args.next_scheduled_date is expected


@pytest.mark.parametrize('test_input, expected', [
    ('-R', True),
    ('--reconciled-status', True),
    ('', False),
])
def test_args_reconciled_status(test_input, expected):
    options = ['-f', 'gargle']
    if test_input:
        options.append(test_input)
    args = ledgerbil.get_args(options)
    assert args.reconciled_status is expected
