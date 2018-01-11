import os
from datetime import date
from unittest import TestCase

from dateutil.relativedelta import relativedelta

from .. import ledgerbil, util
from ..ledgerthing import DATE_AND_PAYEE
from .filetester import FileTester as FT
from .helpers import Redirector
from .schedulething_tester import ScheduleThingTester
from .test_schedulefile import ScheduleFileTests


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
            'error: -S/--schedule-file is required',
            self.redirecterr.getvalue().strip()
        )

    def test_main_file_required(self):
        ledgerbil.main([])
        self.assertEqual(
            'error: -f/--file is required',
            self.redirecterr.getvalue().strip()
        )


class Scheduler(ScheduleThingTester):

    @staticmethod
    def get_schedule_file(the_date, schedule, enter_days=7):
        return (
            ';; scheduler ; enter {enter_days} days\n'
            '\n'
            '{date} bananas unlimited\n'
            '    ;; schedule ; {schedule}\n'
            '    e: misc\n'
            '    l: credit card                     $-50\n\n'.format(
                date=the_date,
                schedule=schedule,
                enter_days=enter_days
            )
        )

    @staticmethod
    def get_ledger_file(the_date):
        return (
            '{date} bananas unlimited\n'
            '    e: misc\n'
            '    l: credit card                     $-50\n\n'.format(
                date=the_date
            )
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
            '--schedule-file', tempschedulefile,
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
        with FT.temp_input(ScheduleFileTests.scheduledata) as tempfile:
            ledgerbil.main(['-n', '-S', tempfile])

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
            'Unhandled multiple statuses: {}'.format(
                DATE_AND_PAYEE.format(
                    date='2016/10/08',
                    payee='zillion'
                )
            ),
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
