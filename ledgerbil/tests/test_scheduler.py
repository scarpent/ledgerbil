from datetime import date
from textwrap import dedent
from unittest import mock

from dateutil.relativedelta import relativedelta

from .. import scheduler, util
from ..ledgerfile import LedgerFile
from .filetester import FileTester
from .test_schedulefile import schedule_testdata


def get_schedule_file(the_date, schedule, enter_days=7):
    return (
        f';; scheduler ; enter {enter_days} days\n'
        '\n'
        f'{the_date} bananas unlimited\n'
        f'    ;; schedule ; {schedule}\n'
        '    e: misc\n'
        '    l: credit card                     $-50\n\n'
    )


def run_it(before_date, after_date, schedule, enter_days=7):
    schedulefiledata = get_schedule_file(
        util.get_date_string(before_date),
        schedule,
        enter_days
    )
    with FileTester.temp_input(schedulefiledata) as temp_schedule_filename:
        with FileTester.temp_input('') as temp_ledger_filename:

            ledgerfile = LedgerFile(temp_ledger_filename)
            return_value = scheduler.run_scheduler(
                ledgerfile,
                temp_schedule_filename
            )
            assert not return_value

            actual_data = FileTester.read_file(temp_schedule_filename)
            expected_data = get_schedule_file(
                util.get_date_string(after_date),
                schedule,
                enter_days
            )

    assert actual_data == expected_data


def test_weekly():
    run_it(
        date.today() - relativedelta(days=7),
        date.today() + relativedelta(days=21),
        'weekly ;; every 2 weeks'
    )


def test_bimonthly():
    lastmonth = date.today() - relativedelta(months=1)
    testdate = date(lastmonth.year, lastmonth.month, 15)

    run_it(
        testdate,
        testdate + relativedelta(months=2),
        'bimonthly'
    )


def test_quarterly():
    lastmonth = date.today() - relativedelta(months=1)
    testdate = date(lastmonth.year, lastmonth.month, 15)

    run_it(
        testdate,
        testdate + relativedelta(months=3),
        'quarterly'
    )


def test_biannual():
    lastmonth = date.today() - relativedelta(months=1)
    testdate = date(lastmonth.year, lastmonth.month, 15)

    run_it(
        testdate,
        testdate + relativedelta(months=6),
        'biannual'
    )


def test_run_enter_days_less_than_one():
    schedulefiledata = FileTester.read_file(
        FileTester.test_enter_lessthan1
    )
    with FileTester.temp_input(schedulefiledata) as temp_schedule_filename:
        with FileTester.temp_input('') as temp_ledger_file:

            ledgerfile = LedgerFile(temp_ledger_file)
            return_value = scheduler.run_scheduler(
                ledgerfile,
                temp_schedule_filename
            )
            assert not return_value

            actual_data = FileTester.read_file(temp_schedule_filename)
            expected_data = schedulefiledata

    assert actual_data == expected_data


@mock.patch(__name__ + '.scheduler.handle_error')
def test_scheduler_error(mock_error):
    schedulefiledata = ';; scheduler enter 321 days'
    with FileTester.temp_input(schedulefiledata) as temp_schedule_filename:
        ledgerfile = None  # is going to error before we use ledgerfile
        scheduler.run_scheduler(
            ledgerfile,
            temp_schedule_filename
        )
        expected = dedent('''\
            Invalid schedule file config:
            ;; scheduler enter 321 days
            Expected:
            ;; scheduler ; enter N days''')
        mock_error.assert_called_once_with(expected)


@mock.patch(__name__ + '.scheduler.print')
def test_next_scheduled_date(mock_print):
    with FileTester.temp_input(schedule_testdata) as tempfile:
        return_value = scheduler.print_next_scheduled_date(tempfile)
    assert return_value is None
    mock_print.assert_called_once_with('2007/07/07')


@mock.patch(__name__ + '.scheduler.print')
def test_next_scheduled_date_no_next(mock_print):
    with FileTester.temp_input(';; scheduler ; enter 45 days') as tempfile:
        return_value = scheduler.print_next_scheduled_date(tempfile)
    assert return_value is None
    mock_print.assert_called_once_with('')


@mock.patch(__name__ + '.scheduler.handle_error')
def test_next_scheduled_date_scheduler_exception(mock_error):
    schedulefile_data = ';; scheduler enter 567 days'
    with FileTester.temp_input(schedulefile_data) as temp_schedule_filename:
        scheduler.print_next_scheduled_date(
            temp_schedule_filename
        )
        expected = dedent('''\
                Invalid schedule file config:
                ;; scheduler enter 567 days
                Expected:
                ;; scheduler ; enter N days''')
        mock_error.assert_called_once_with(expected)
