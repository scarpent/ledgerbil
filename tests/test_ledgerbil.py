#!/usr/bin/python

"""unit tests for ledgerbil.py"""

import os

from datetime import date
from dateutil.relativedelta import relativedelta
from unittest import TestCase

import ledgerbil

from filetester import FileTester as FT
from ledgerthing import LedgerThing
from redirector import Redirector


__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class MainBasicInput(TestCase):

    def testMainNoOptionsOnSortedFile(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_sortedfile)
        ledgerbil.main(['--file', tempfile])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)

    def testMainNoOptionsOnUnsortedFile(self):
        """main should parse and write unsorted file unchanged"""
        expected = FT.readFile(FT.alpha_unsortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_unsortedfile)
        ledgerbil.main(['--file', tempfile])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)


class Sorting(TestCase):

    def testMainSortOnSortedFile(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_sortedfile)
        ledgerbil.main(['--file', tempfile, '--sort'])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)

    def testMainSortedNoOptions(self):
        """main should parse unsorted file and write sorted file"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_unsortedfile)
        ledgerbil.main(['--file', tempfile, '--sort'])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)


class Scheduler(Redirector):

    @staticmethod
    def get_schedule_file(the_date, schedule, enter_days=7):
        return (
            ';; scheduler ; enter {enter_days} days\n'
            '\n'
            '{date} bananas unlimited\n'
            '    ;; schedule ; {schedule}\n'
            '    e: misc\n'
            '    l: credit card                     $-50\n'.format(
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
            '    l: credit card                     $-50\n'.format(
                date=the_date
            )
        )

    def test_scheduler(self):
        lastmonth = date.today() - relativedelta(months=1)
        testdate = date(lastmonth.year, lastmonth.month, 15)
        schedule = 'monthly ;; every 2 months'

        schedulefiledata = self.get_schedule_file(
            LedgerThing.getDateString(testdate),
            schedule
        )
        tempschedulefile = FT.writeToTempFile(
            FT.testdir + 'test_scheduler_schedule_file',
            schedulefiledata
        )

        templedgerfile = FT.writeToTempFile(
            FT.testdir + 'test_scheduler_ledger_file',
            ''
        )

        ledgerbil.main([
            '--file', templedgerfile,
            '--schedule-file', tempschedulefile,
        ])

        schedulefile_actual = FT.readFile(tempschedulefile)
        schedulefile_expected = self.get_schedule_file(
            LedgerThing.getDateString(
                testdate + relativedelta(months=2)
            ),
            schedule
        )

        ledgerfile_actual = FT.readFile(templedgerfile)
        ledgerfile_expected = self.get_ledger_file(
            LedgerThing.getDateString(testdate)
        )

        os.remove(tempschedulefile)
        os.remove(templedgerfile)

        self.assertEqual(schedulefile_expected, schedulefile_actual)
        self.assertEqual(ledgerfile_expected, ledgerfile_actual)
