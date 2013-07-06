#!/usr/bin/python

"""unit test for schedulething.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from datetime import datetime
from datetime import date
from datetime import timedelta

from schedulething import ScheduleThing
from ledgerthing import LedgerThing


class GetNextDate(unittest.TestCase):

    scheduleLineFileConfig = [';; scheduler ; enter 7 days ; preview 30 days']
    ScheduleThing.doFileConfig = True
    scheduleThingFileConfig = ScheduleThing(scheduleLineFileConfig)

    def testGetNextDateMonthlyThisMonthEom(self):

        scheduleLines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; monthly ; eom ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/06/30')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyThisMonthEomOnTheDay(self):

        scheduleLines = [
            '2013/06/30 lightning energy',
            '    ;; schedule ; monthly ; eom ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/31')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyNextMonthEom30(self):

        scheduleLines = [
            '2013/07/30 lightning energy',
            '    ;; schedule ; monthly ; eom30 ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/08/30')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyThisMonth(self):

        scheduleLines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto',
        ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/06/12')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyNextMonth(self):

        scheduleLines = [
            '2013/06/17 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/12')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyNextMonthAgain(self):

        scheduleLines = [
            '2013/06/12 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/12')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyNextMonthFirst(self):

        scheduleLines = [
            '2013/06/28 lightning energy',
            '    ;; schedule ; monthly ; 1st',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/01')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyMultipleDaysThisMonth(self):

        scheduleLines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; monthly ; 7th, 12th ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/06/07')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyMultipleDaysThisMonthAgain(self):

        scheduleLines = [
            '2013/06/08 lightning energy',
            '    ;; schedule ; monthly ; 7th, 12th'
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/06/12')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyMultipleDaysNextMonth(self):

        scheduleLines = [
            '2013/06/27 lightning energy',
            '    ;; schedule ; monthly ; 7th, 27th ; ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/07')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyInterval3(self):

        scheduleLines = [
            '2013/06/15 lightning energy',
            '    ;; schedule ; month ; 15th ; 3 ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/09/15')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyInterval12eomLeapOne(self):

        scheduleLines = [
            '2011/02/28 lightning energy',
            '    ;; schedule ; month ; eom ; 12 ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2012/02/29')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyInterval12eomLeapTwo(self):

        scheduleLines = [
            '2012/02/29 lightning energy',
            '    ;; schedule ; month ; eom ; 12 ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/02/28')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyTooMany29(self):

        scheduleLines = [
            '2013/01/31 lightning energy',
            '    ;; schedule ; month ; 29th ; 1 ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/02/28')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyTooMany30(self):

        scheduleLines = [
            '2013/01/30 lightning energy',
            '    ;; schedule ; month ; 30th ; 1 ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/02/28')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )

    def testGetNextDateMonthlyTooMany70(self):

        scheduleLines = [
            '2013/07/15 lightning energy',
            '    ;; schedule ; month ; 70th ; 1 ; auto',
            ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/31')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )


class GetWeekDay(unittest.TestCase):

    scheduleLinesTest = [
        '2013/06/29 lightning energy',
        '    ;; schedule ; monthly ; 12th ; ; auto'
    ]

    ScheduleThing.doFileConfig = False
    scheduleThing = ScheduleThing(scheduleLinesTest)

    def testGetWeekDay(self):
        self.assertEqual(-1, self.scheduleThing._getWeekDay())


class GetMonthDay(unittest.TestCase):

    scheduleLinesTest = [
        '2013/06/29 lightning energy',
        '    ;; schedule ; monthly ; 12th ; ; auto'
    ]

    ScheduleThing.doFileConfig = False
    scheduleThing = ScheduleThing(scheduleLinesTest)

    def testGetMonthDayNormal(self):
        """normal day is returned as the same day number"""
        testdate = datetime.strptime('2013/06/16', '%Y/%m/%d')
        self.assertEqual(5, self.scheduleThing._getMonthDay('5', testdate))

    def testGetMonthDayJuneEom(self):
        """eom for a 30-day month is 30"""
        testdate = datetime.strptime('2013/06/16', '%Y/%m/%d')
        self.assertEqual(
            30,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM, testdate)
        )

    def testGetMonthDayJulyEom(self):
        """eom for a 31-day month is 31"""
        testdate = datetime.strptime('2013/07/01', '%Y/%m/%d')
        self.assertEqual(
            31,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM, testdate)
        )

    def testGetMonthDayFebruaryEom(self):
        """eom for a non-leap year february is 28"""
        testdate = datetime.strptime('2013/02/05', '%Y/%m/%d')
        self.assertEqual(
            28,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM, testdate)
        )

    def testGetMonthDayLeapFebruaryEom(self):
        """eom for a leap year february is 29"""
        testdate = datetime.strptime('2012/02/05', '%Y/%m/%d')
        self.assertEqual(
            29,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM, testdate)
        )

    def testGetMonthDayJuneEom30(self):
        """eom30 for a 30-day month is 30"""
        testdate = datetime.strptime('2013/06/16', '%Y/%m/%d')
        self.assertEqual(
            30,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM30, testdate)
        )

    def testGetMonthDayJulyEom30(self):
        """eom30 for a 31-day month is 30"""
        testdate = datetime.strptime('2013/07/01', '%Y/%m/%d')
        self.assertEqual(
            30,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM30, testdate)
        )

    def testGetMonthDayFebruaryEom30(self):
        """eom30 for a non-leap year february is 28"""
        testdate = datetime.strptime('2013/02/05', '%Y/%m/%d')
        self.assertEqual(
            28,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM30, testdate)
        )

    def testGetMonthDayLeapFebruaryEom30(self):
        """eom for a leap year february is 29"""
        testdate = datetime.strptime('2012/02/05', '%Y/%m/%d')
        self.assertEqual(
            29,
            self.scheduleThing._getMonthDay(ScheduleThing.EOM30, testdate)
        )
