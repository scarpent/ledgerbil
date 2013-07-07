#!/usr/bin/python

"""unit test for schedulething.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest

from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

from schedulething import ScheduleThing
from ledgerthing import LedgerThing
from ledgerbilexceptions import *

class HandleThingConfig(unittest.TestCase):

    def setUp(self):
        scheduleLineFileConfig = [';; scheduler ; enter 7 days ; preview 30 days']
        ScheduleThing.doFileConfig = True
        ScheduleThing(scheduleLineFileConfig)

    def getExpectedConfig(self, intervaluom, days, interval):
        return '%s | %s | %s' % (intervaluom, days, interval)

    def getActualConfig(self, schedulething):
        return (
            '%s | %s | %s' % (
                schedulething.intervalUom,
                schedulething.days,
                schedulething.interval
            )
        )

    def testBasicThingConfig(self):

        schedulelines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; monthly ; eom30 2 15 ; 3 ; auto',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [2, 15, 'eom30'], 3
            ),
            self.getActualConfig(schedulething)
        )

    def testNotEnoughParameters(self):

        schedulelines = [
            '2013/06/05 lightning energy',
            '    ;; schedule',
            ]
        with self.assertRaises(LdgNotEnoughParametersError):
            ScheduleThing(schedulelines)

    def testScheduleLabelNotRight(self):

        schedulelines = [
            '2013/06/05 lightning energy',
            #'    ;; scheduled ; monthly ; eom30 2 15 ; 3 ; auto',
            '    ;; scheduble ; monthly',
        ]
        with self.assertRaises(Exception):
            ScheduleThing(schedulelines)

class HandleFileConfig(unittest.TestCase):

    # to do, maybe have this like redirector, to be included different places
    def setUp(self):
        ScheduleThing.doFileConfig = True
        ScheduleThing.enterDays = ScheduleThing.NO_DAYS
        ScheduleThing.previewDays = ScheduleThing.NO_DAYS
        ScheduleThing.entryBoundaryDate = None
        ScheduleThing.previewBoundaryDate = None

    def getExpectedConfig(self, enterdays, previewdays):
        return (
            '%s | %s | %s | %s' % (
                enterdays,
                previewdays,
                LedgerThing.getDateString(
                    date.today() + relativedelta(days=enterdays)
                ),
                LedgerThing.getDateString(
                    date.today() + relativedelta(days=previewdays)
                )
            )
        )

    def getActualConfig(self, schedulething):
        return (
            '%s | %s | %s | %s' % (
                schedulething.enterDays,
                schedulething.previewDays,
                LedgerThing.getDateString(
                    schedulething.entryBoundaryDate
                ),
                LedgerThing.getDateString(
                    schedulething.previewBoundaryDate
                )
            )
        )

    def testBasicFileConfig(self):
        scheduleLineFileConfig = [
            ';; scheduler ; enter 7 days ; preview 30 days'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(7, 30),
            self.getActualConfig(schedulething)
        )

    def testInvalidFileConfig(self):
            scheduleLineFileConfig = [
                ';; shceduler ; enter 7 days ; preview 30 days'
            ]
            with self.assertRaises(Exception):
                ScheduleThing(scheduleLineFileConfig)

    def testFileConfigNoPreview(self):
        scheduleLineFileConfig = [
                ';;scheduler;enter 7 days;;'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(7, ScheduleThing.NO_DAYS),
            self.getActualConfig(schedulething)
        )

    def testFileConfigNoEnter(self):
        scheduleLineFileConfig = [
            ';;scheduler;preview 60 days;;'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(ScheduleThing.NO_DAYS, 60),
            self.getActualConfig(schedulething)
        )

    def testFileConfigNoEnterNoPreview(self):
        scheduleLineFileConfig = [
            ';;scheduler'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.NO_DAYS,
                ScheduleThing.NO_DAYS
            ),
            self.getActualConfig(schedulething)
        )

    def testFileConfigPreviewLessThanEnter(self):
        scheduleLineFileConfig = [
            ';;   scheduler   ; enter 40 day    ; preview 30 day ; comment'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(40, ScheduleThing.NO_DAYS),
            self.getActualConfig(schedulething)
        )

    def testFileConfigPreviewEqualsEnter(self):
        scheduleLineFileConfig = [
            ';;   scheduler   ; enter 50 day    ; preview 50 day ; comment'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(50, ScheduleThing.NO_DAYS),
            self.getActualConfig(schedulething)
        )

    def testFileConfigEnterLessThanOne(self):
        scheduleLineFileConfig = [
            ';;   scheduler   ; enter 0 day    ; preview 90 day ; comment'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(ScheduleThing.NO_DAYS, 90),
            self.getActualConfig(schedulething)
        )


class GetNextDate(unittest.TestCase):

    def setUp(self):
        scheduleLineFileConfig = [';; scheduler ; enter 7 days ; preview 30 days']
        ScheduleThing.doFileConfig = True
        ScheduleThing(scheduleLineFileConfig)

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

    def setUp(self):
        scheduleLinesTest = [
            '2013/06/29 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto'
        ]

        ScheduleThing.doFileConfig = False
        self.scheduleThing = ScheduleThing(scheduleLinesTest)

    def testGetWeekDay(self):
        self.assertEqual(-1, self.scheduleThing._getWeekDay())


class GetMonthDay(unittest.TestCase):

    def setUp(self):
        scheduleLinesTest = [
            '2013/06/29 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto'
        ]

        ScheduleThing.doFileConfig = False
        self.scheduleThing = ScheduleThing(scheduleLinesTest)

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
