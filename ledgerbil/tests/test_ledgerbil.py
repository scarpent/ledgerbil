from datetime import date
from textwrap import dedent
from unittest import mock

import pytest
from dateutil.relativedelta import relativedelta

from ..ledgerbilexceptions import ERROR_RETURN_VALUE
from . import filetester as FT
from .helpers import Redirector
from .test_schedulefile import schedule_testdata

from .. import (  # noqa: F401 (stuff used in patches) isort:skip
    ledgerbil,
    reconciler,
    scheduler,
    settings,
    settings_getter,
    util,
)


@pytest.mark.parametrize("test_input", [FT.alpha_sortedfile, FT.alpha_unsortedfile])
def test_main_no_options(test_input):
    """main should parse and write sorted and unsorted files unchanged"""
    expected = FT.read_file(test_input)
    with FT.temp_file(expected) as templedgerfile:
        ledgerbil.main(["--file", templedgerfile])
        actual = FT.read_file(templedgerfile)
    assert actual == expected


@pytest.mark.parametrize("test_input", [FT.alpha_sortedfile, FT.alpha_unsortedfile])
def test_main_sort(test_input):
    """main should write sorted file"""
    testdata = FT.read_file(test_input)
    with FT.temp_file(testdata) as templedgerfile:
        ledgerbil.main(["--file", templedgerfile, "--sort"])
        actual = FT.read_file(templedgerfile)

    expected = FT.read_file(FT.alpha_sortedfile)
    assert actual == expected


def test_main_sort_different_date_format():
    """main should fail to sort file if date format is different
       than in ledger entries"""

    class MockSettings:
        DATE_FORMAT = "%Y-%m-%d"

    settings_getter.settings = MockSettings()
    expected = FT.read_file(FT.alpha_unsortedfile)
    with FT.temp_file(expected) as templedgerfile:
        ledgerbil.main(["--file", templedgerfile, "--sort"])
        actual = FT.read_file(templedgerfile)

    assert actual == expected
    settings_getter.settings = settings.Settings()


@mock.patch(__name__ + ".ledgerbil.LedgerFile.write_file")
@mock.patch(__name__ + ".ledgerbil.LedgerFile.sort")
@mock.patch(__name__ + ".ledgerbil.LedgerFile.__init__")
def test_sorting_multiple_files(mock_init, mock_sort, mock_write_file):
    mock_init.return_value = None
    with FT.temp_file("; no data 1") as file1:
        with FT.temp_file("; no data 2") as file2:
            ledgerbil.main(["--file", file1, "--file", file2, "--sort"])

    assert mock_init.call_args_list == [mock.call(file1, None), mock.call(file2, None)]
    # It would be nice to be able to further confirm that each instance
    # of Ledgerfile called these methods
    assert mock_sort.call_args_list == [mock.call(), mock.call()]
    assert mock_write_file.call_args_list == [mock.call(), mock.call()]


class MainErrors(Redirector):
    def test_main_next_scheduled_date(self):
        ledgerbil.main(["--next-scheduled-date"])
        expected = "error: -s/--schedule is required"
        assert self.redirecterr.getvalue().strip() == expected

    def test_main_file_required(self):
        ledgerbil.main([])
        expected = "error: -f/--file is required"
        assert self.redirecterr.getvalue().strip() == expected


def get_schedule_file(the_date, schedule, enter_days=7):
    return (
        f";; scheduler ; enter {enter_days} days\n"
        "\n"
        f"{the_date} bananas unlimited\n"
        f"    ;; schedule ; {schedule}\n"
        "    e: misc\n"
        "    l: credit card                     $-50\n\n"
    )


def get_ledger_file(the_date):
    return (
        f"{the_date} bananas unlimited\n"
        "    e: misc\n"
        "    l: credit card                     $-50\n\n"
    )


def test_scheduler():
    lastmonth = date.today() - relativedelta(months=1)
    testdate = date(lastmonth.year, lastmonth.month, 15)
    schedule = "monthly ;; every 2 months"

    schedulefiledata = get_schedule_file(util.get_date_string(testdate), schedule)
    with FT.temp_file(schedulefiledata) as tempschedulefile:
        with FT.temp_file("") as templedgerfile:
            ledgerbil.main(["--file", templedgerfile, "--schedule", tempschedulefile])

            schedulefile_actual = FT.read_file(tempschedulefile)
            schedulefile_expected = get_schedule_file(
                util.get_date_string(testdate + relativedelta(months=2)), schedule
            )
            assert schedulefile_actual == schedulefile_expected

            ledgerfile_actual = FT.read_file(templedgerfile)
            ledgerfile_expected = get_ledger_file(util.get_date_string(testdate))
            assert ledgerfile_actual == ledgerfile_expected


class Scheduler(Redirector):
    @mock.patch(__name__ + ".ledgerbil.LedgerFile")
    def test_next_scheduled_date(self, mock_ledgerfile):
        with FT.temp_file(schedule_testdata) as tempfile:
            ledgerbil.main(["-n", "-s", tempfile])
        assert self.redirect.getvalue() == "2007/07/07\n"
        assert not mock_ledgerfile.called


@mock.patch(__name__ + ".ledgerbil.run_scheduler")
def test_scheduler_multiple_files(mock_scheduler):
    """The first ledger file should be used by the scheduler
       if more than one is passed in"""
    with FT.temp_file("; schedule file") as schedule_filename:
        with FT.temp_file("; ledger file") as ledger_filename:
            with FT.temp_file("; ledger file 2") as ledger2_filename:
                ledgerbil.main(
                    [
                        "--file",
                        ledger_filename,
                        "--file",
                        ledger2_filename,
                        "--schedule",
                        schedule_filename,
                    ]
                )

            mock_scheduler.assert_called_once()
            assert mock_scheduler.call_args[0][0].filename == ledger_filename
            assert mock_scheduler.call_args[0][1] == schedule_filename


@mock.patch(__name__ + ".ledgerbil.LedgerFile.sort")
@mock.patch(__name__ + ".ledgerbil.run_scheduler")
def test_scheduler_and_sort_can_be_called_together(mock_scheduler, mock_sort):
    mock_scheduler.return_value = None
    with FT.temp_file("; schedule file") as schedule_filename:
        with FT.temp_file("; ledger file") as ledger_filename:
            ledgerbil.main(
                ["--file", ledger_filename, "--schedule", schedule_filename, "--sort"]
            )

    mock_scheduler.assert_called_once()
    mock_sort.assert_called_once()


@mock.patch(__name__ + ".ledgerbil.LedgerFile.sort")
@mock.patch(__name__ + ".ledgerbil.run_scheduler")
def test_scheduler_runs_before_sort(mock_scheduler, mock_sort):
    # By not setting a return_value for mock_scheduler, the return
    # value will be a mock which will appear as an error in the code
    # and cause a return before the sort is reached
    with FT.temp_file("; schedule file") as schedule_filename:
        with FT.temp_file("; ledger file") as ledger_filename:
            ledgerbil.main(
                ["--file", ledger_filename, "--schedule", schedule_filename, "--sort"]
            )

    mock_scheduler.assert_called_once()
    assert not mock_sort.called


class ReconcilerTests(Redirector):
    def test_multiple_matches(self):
        # in different transactions
        ledgerbil.main(
            ["--file", FT.test_rec_multiple_match, "--reconcile", "checking"]
        )
        expected = dedent(
            """\
            More than one matching account:
                a: checking down
                a: checking up
            """
        )
        assert self.redirecterr.getvalue() == expected

        # in same transaction
        self.reset_err_redirect()
        ledgerbil.main(["--file", FT.test_rec_multiple_match, "--reconcile", "cash"])
        expected = dedent(
            """\
            More than one matching account:
                a: cash in
                a: cash out
            """
        )
        assert self.redirecterr.getvalue() == expected

    def test_multiple_statuses(self):
        ledgerbil.main(
            ["--file", FT.test_rec_multiple_match, "--reconcile", "mattress"]
        )
        expected = "Unhandled multiple statuses: 2016/10/08 zillion\n"
        assert self.redirecterr.getvalue() == expected

    def test_no_matching_account(self):
        result = ledgerbil.main(
            ["--file", FT.test_reconcile, "--reconcile", "schenectady schmectady"]
        )
        expected = 'No matching account found for "schenectady schmectady"\n'
        assert self.redirect.getvalue() == expected
        assert result is None

    def test_no_matching_account_in_multiple(self):
        result = ledgerbil.main(
            [
                "--file",
                FT.test_reconcile,
                "--file",
                FT.test_reconcile,
                "--reconcile",
                "schenectady schmectady",
            ]
        )
        expected = 'No matching account found for "schenectady schmectady"\n'
        assert self.redirect.getvalue() == expected
        assert result is None


@mock.patch(__name__ + ".ledgerbil.LedgerFile.sort")
@mock.patch(__name__ + ".ledgerbil.run_scheduler")
@mock.patch(__name__ + ".ledgerbil.matching_account_found")
@mock.patch(__name__ + ".ledgerbil.run_reconciler")
def test_reconciler_takes_precedence_over_scheduler_and_sort(
    mock_reconciler, mock_match, mock_scheduler, mock_sort
):
    mock_scheduler.return_value = None
    mock_match.return_value = True
    with FT.temp_file("; schedule file") as schedule_filename:
        with FT.temp_file("; ledger file") as ledger_filename:
            ledgerbil.main(
                [
                    "--file",
                    ledger_filename,
                    "--schedule",
                    schedule_filename,
                    "--reconcile",
                    "abc",
                    "--sort",
                ]
            )

    mock_reconciler.assert_called_once()
    assert not mock_scheduler.called
    assert not mock_sort.called


@mock.patch(__name__ + ".ledgerbil.run_reconciler")
def test_run_reconciler_called(mock_run_reconciler):
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment
    """
    )
    with FT.temp_file(ledgerfile_data) as tempfilename:
        ledgerbil.main(["--file", tempfilename, "--reconcile", "bonds"])
    mock_run_reconciler.assert_called_once()


@mock.patch(__name__ + ".ledgerbil.LedgerFile")
@mock.patch(__name__ + ".ledgerbil.handle_error")
@mock.patch(__name__ + ".ledgerbil.reconciled_status")
def test_reconciled_status(mock_reconciled, mock_error, mock_ledgerfile):
    # reconciled status takes precedence over calling subsequent stuff
    ledgerbil.main(["--reconciled-status"])
    assert not mock_error.called
    assert not mock_ledgerfile.called
    mock_reconciled.assert_called_once_with()


@mock.patch(__name__ + ".reconciler.util.handle_error")
def test_reconciler_exception(mock_handle_error):
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    """
    )
    with FT.temp_file(ledgerfile_data) as tempfilename:
        ledgerbil.main(["--file", tempfilename, "--reconcile", "bonds"])
    expected = 'Unhandled shares with non-shares: "a: 401k: bonds idx"'
    mock_handle_error.assert_called_once_with(expected)


def test_reconciler_exception_return_value():
    ledgerfile_data = dedent(
        """
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    """
    )
    with FT.temp_file(ledgerfile_data) as tempfilename:
        return_value = ledgerbil.main(["--file", tempfilename, "--reconcile", "bonds"])
    assert return_value == ERROR_RETURN_VALUE


@mock.patch(__name__ + ".ledgerbil.handle_error")
def test_main_investments_with_argv_none(mock_handle_error):
    with mock.patch("sys.argv", ["/script"]):
        ledgerbil.main()
    expected = "error: -f/--file is required"
    mock_handle_error.assert_called_once_with(expected)


def test_main_investments_with_argv_none_retun_value():
    with mock.patch("sys.argv", ["/script"]):
        assert ledgerbil.main() == ERROR_RETURN_VALUE


@mock.patch(__name__ + ".scheduler.handle_error")
def test_next_scheduled_date_scheduler_exception(mock_handle_error):
    schedulefile_data = ";; scheduler enter 567 days"
    with FT.temp_file(schedulefile_data) as tempfilename:
        ledgerbil.main(["--schedule", tempfilename, "-n"])
    expected = dedent(
        """\
            Invalid schedule file config:
            ;; scheduler enter 567 days
            Expected:
            ;; scheduler ; enter N days"""
    )
    mock_handle_error.assert_called_once_with(expected)


def test_next_scheduled_date_scheduler_exception_return_value():
    schedulefile_data = ";; scheduler enter 567 days"
    with FT.temp_file(schedulefile_data) as tempfilename:
        assert ledgerbil.main(["--schedule", tempfilename, "-n"]) == ERROR_RETURN_VALUE


@mock.patch(__name__ + ".scheduler.handle_error")
def test_scheduler_exception(mock_handle_error):
    with FT.temp_file(";; scheduler enter 321 days") as tempfilename:
        ledgerbil.main(["--schedule", tempfilename, "-f", FT.testfile])
    expected = dedent(
        """\
        Invalid schedule file config:
        ;; scheduler enter 321 days
        Expected:
        ;; scheduler ; enter N days"""
    )
    mock_handle_error.assert_called_once_with(expected)


def test_scheduler_exception_return_value():
    with FT.temp_file(";; scheduler enter 321 days") as tempfilename:
        return_value = ledgerbil.main(["--schedule", tempfilename, "-f", FT.testfile])
    assert return_value == ERROR_RETURN_VALUE


@mock.patch(__name__ + ".ledgerbil.argparse.ArgumentParser.print_help")
def test_args_no_parameters(mock_print_help):
    ledgerbil.get_args([])
    mock_print_help.assert_called_once()


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ([], []),
        (["-f", "bob"], ["bob"]),
        (["--file", "loblaw"], ["loblaw"]),
        (["-f", "bob", "-f", "loblaw"], ["bob", "loblaw"]),
    ],
)
def test_args_file_option(test_input, expected):
    args = ledgerbil.get_args(test_input)
    assert args.file == expected


def test_args_file_option_and_filename_both_required():
    """should cause argparse error if file opt specified without file"""
    with pytest.raises(SystemExit) as excinfo:
        ledgerbil.get_args(["--file"])
    assert str(excinfo.value) == "2"


@pytest.mark.parametrize(
    "test_input, expected", [("-S", True), ("--sort", True), ("", False)]
)
def test_args_sort_option(test_input, expected):
    options = ["-f", "mario"]
    if test_input:
        options.append(test_input)
    args = ledgerbil.get_args(options)
    assert args.sort is expected


@pytest.mark.parametrize(
    "test_input, expected", [("-s", "robo"), ("--schedule", "cop")]
)
def test_args_schedule_file_option(test_input, expected):
    args = ledgerbil.get_args([test_input, expected])
    assert args.schedule == expected


def test_args_schedule_filename_required_with_schedule_option():
    """argparse error if sched file opt specified without file"""
    with pytest.raises(SystemExit) as excinfo:
        ledgerbil.get_args(["--schedule"])
    assert str(excinfo.value) == "2"


@pytest.mark.parametrize(
    "test_input, expected", [("-n", True), ("--next-scheduled-date", True), ("", False)]
)
def test_args_next_scheduled_date(test_input, expected):
    options = ["-f", "gargle"]
    if test_input:
        options.append(test_input)
    args = ledgerbil.get_args(options)
    assert args.next_scheduled_date is expected


@pytest.mark.parametrize(
    "test_input, expected", [("-R", True), ("--reconciled-status", True), ("", False)]
)
def test_args_reconciled_status(test_input, expected):
    options = ["-f", "gargle"]
    if test_input:
        options.append(test_input)
    args = ledgerbil.get_args(options)
    assert args.reconciled_status is expected
