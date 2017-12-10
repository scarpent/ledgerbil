"""unit test for scheduler.py"""

import os
from datetime import date

from dateutil.relativedelta import relativedelta

from .. import util
from ..ledgerfile import LedgerFile
from ..schedulefile import ScheduleFile
from ..scheduler import Scheduler
from .filetester import FileTester
from .schedulething_tester import ScheduleThingTester


class SchedulerRun(ScheduleThingTester):

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

    def run_it(self, before_date, after_date, schedule, enter_days=7):
        schedulefiledata = self.get_schedule_file(
            util.get_date_string(before_date),
            schedule,
            enter_days
        )
        tempschedulefile = FileTester.write_to_temp_file(
            FileTester.testdir + 'run_it_schedule_file',
            schedulefiledata
        )
        schedulefile = ScheduleFile(tempschedulefile)

        templedgerfile = FileTester.write_to_temp_file(
            FileTester.testdir + 'run_it_ledger_file',
            ''
        )
        ledgerfile = LedgerFile(templedgerfile)

        scheduler = Scheduler(ledgerfile, schedulefile)
        scheduler.run()

        ledgerfile.write_file()
        schedulefile.write_file()

        schedulefile_actual = FileTester.read_file(tempschedulefile)

        schedulefile_expected = self.get_schedule_file(
            util.get_date_string(after_date),
            schedule,
            enter_days
        )

        os.remove(templedgerfile)
        os.remove(tempschedulefile)

        self.assertEqual(schedulefile_expected, schedulefile_actual)

    def test_weekly(self):
        self.run_it(
            date.today() - relativedelta(days=7),
            date.today() + relativedelta(days=21),
            'weekly ;; every 2 weeks'
        )

    def test_bimonthly(self):
        lastmonth = date.today() - relativedelta(months=1)
        testdate = date(lastmonth.year, lastmonth.month, 15)

        self.run_it(
            testdate,
            testdate + relativedelta(months=2),
            'bimonthly'
        )

    def test_quarterly(self):
        lastmonth = date.today() - relativedelta(months=1)
        testdate = date(lastmonth.year, lastmonth.month, 15)

        self.run_it(
            testdate,
            testdate + relativedelta(months=3),
            'quarterly'
        )

    def test_biannual(self):
        lastmonth = date.today() - relativedelta(months=1)
        testdate = date(lastmonth.year, lastmonth.month, 15)

        self.run_it(
            testdate,
            testdate + relativedelta(months=6),
            'biannual'
        )

    def testRunEnterDaysLessThanOne(self):
        schedulefiledata = FileTester.read_file(
            FileTester.test_enter_lessthan1
        )
        tempschedulefile = FileTester.write_to_temp_file(
            FileTester.test_enter_lessthan1,
            schedulefiledata
        )
        schedulefile = ScheduleFile(tempschedulefile)

        templedgerfile = FileTester.create_temp_file('')
        ledgerfile = LedgerFile(templedgerfile)

        scheduler = Scheduler(ledgerfile, schedulefile)
        scheduler.run()

        ledgerfile.write_file()
        schedulefile.write_file()

        schedulefile_actual = FileTester.read_file(tempschedulefile)
        schedulefile_expected = FileTester.read_file(
            FileTester.test_enter_lessthan1
        )

        os.remove(templedgerfile)
        os.remove(tempschedulefile)

        self.assertEqual(
            schedulefile_expected,
            schedulefile_actual
        )
