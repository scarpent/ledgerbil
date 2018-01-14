import os
import sys
from datetime import date
from textwrap import dedent
from unittest import TestCase, mock

import pytest

from dateutil.relativedelta import relativedelta

from .. import ledgerbil, util
from .filetester import FileTester as FT
from .helpers import Redirector
from .test_schedulefile import schedule_testdata


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

    def test_next_scheduled_date(self):
        with FT.temp_input(schedule_testdata) as tempfile:
            ledgerbil.main(['-n', '-s', tempfile])
        assert self.redirect.getvalue().rstrip() == '2007/07/07'


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
        self.assertEqual(0, result)
        self.assertEqual(
            'No matching account found for "schenectady schmectady"',
            self.redirect.getvalue().rstrip()
        )


@mock.patch(__name__ + '.ledgerbil.print')
def test_ledgerbil_error_printer_exiter(mock_print):
    gerbil = ledgerbil.Ledgerbil(None)
    return_code = gerbil.error('blah blah blah')
    mock_print.assert_called_once_with('blah blah blah', file=sys.stderr)
    assert return_code == -1


@mock.patch(__name__ + '.ledgerbil.Reconciler.cmdloop')
def test_reconciler_cmdloop_called(mock_cmdloop):
    ledgerfile_data = dedent('''
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    ''')
    with FT.temp_input(ledgerfile_data) as tempfilename:
        return_code = ledgerbil.main([
            '--file', tempfilename,
            '--reconcile', 'bonds'
        ])
    mock_cmdloop.assert_called_once()
    assert return_code == 0


@mock.patch(__name__ + '.ledgerbil.Ledgerbil.error')
def test_reconciler_exception(mock_error):
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
    mock_error.assert_called_once_with(expected)


@mock.patch(__name__ + '.ledgerbil.Ledgerbil.error')
def test_main_investments_with_argv_none(mock_error):
    with mock.patch('sys.argv', ['/script']):
        ledgerbil.main()
    expected = 'error: -f/--file is required'
    mock_error.assert_called_once_with(expected)


@mock.patch(__name__ + '.ledgerbil.Ledgerbil.error')
def test_next_scheduled_date_scheduler_exception(mock_error):
    schedulefile_data = dedent(';; scheduler enter 567 days')
    with FT.temp_input(schedulefile_data) as tempfilename:
        ledgerbil.main(['--schedule', tempfilename, '-n'])
    expected = dedent('''\
            Invalid schedule file config:
            ;; scheduler enter 567 days
            Expected:
            ;; scheduler ; enter N days''')
    mock_error.assert_called_once_with(expected)


@mock.patch(__name__ + '.ledgerbil.Ledgerbil.error')
def test_scheduler_exception(mock_error):
    schedulefile_data = dedent(';; scheduler enter 321 days')
    with FT.temp_input(schedulefile_data) as tempfilename:
        ledgerbil.main(['--schedule', tempfilename, '-f', FT.testfile])
    expected = dedent('''\
            Invalid schedule file config:
            ;; scheduler enter 321 days
            Expected:
            ;; scheduler ; enter N days''')
    mock_error.assert_called_once_with(expected)


@mock.patch(__name__ + '.ledgerbil.argparse.ArgumentParser.print_help')
def test_args_no_parameters(mock_print_help):
    ledgerbil.get_args([])
    mock_print_help.assert_called_once()


@pytest.mark.parametrize('test_input, expected', [
    ('-f', 'bob'),
    ('--file', 'loblaw'),
])
def test_args_file_option(test_input, expected):
    args = ledgerbil.get_args([test_input, expected])
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
    assert args.next_scheduled_date == expected
