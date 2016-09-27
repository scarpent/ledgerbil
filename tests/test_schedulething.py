#!/usr/bin/python

"""unit test for schedulething.py"""


from unittest import TestCase

from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

from redirector import Redirector
from schedulething import ScheduleThing
from ledgerthing import LedgerThing
from ledgerbilexceptions import *


__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class GetSafeDate(Redirector):

    def setUp(self):
        super(GetSafeDate, self).setUp()
        scheduleLinesTest = [
            '2013/06/29 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto'
        ]
        ScheduleThing.doFileConfig = False
        self.scheduleThing = ScheduleThing(scheduleLinesTest)

    def testDateIsFine(self):
        expected = date(2013, 8, 31)
        actual = self.scheduleThing._getSafeDate(expected, 31)
        self.assertEqual(expected, actual)

    def testDayIsTooMany(self):
        expected = date(2013, 8, 31)
        actual = self.scheduleThing._getSafeDate(date(2013, 8, 31), 99)
        self.assertEqual(expected, actual)


class GetScheduledEntries(Redirector):

    def setUp(self):
        super(GetScheduledEntries, self).setUp()
        scheduleLineFileConfig = [
            ';; scheduler ; enter 7 days'
        ]
        ScheduleThing.doFileConfig = True
        ScheduleThing(scheduleLineFileConfig)

    def testOneEntryCount(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)

        expected = 1
        actual = len(schedulething.getScheduledEntries())

        self.assertEqual(expected, actual)

    def testOneEntryNextDate(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(months=1)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)

    def testOneEntryContent(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)

        expected = [
            '{date} lightning energy'.format(date=testdate),
            '    blah blah blah',
        ]

        actual = schedulething.getScheduledEntries()[0].getLines()

        self.assertEqual(expected, actual)

    def testTwoEntriesCount(self):
        testdate = LedgerThing.getDateString(
            date.today() - relativedelta(months=1)
        )
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)

        expected = 2
        actual = len(schedulething.getScheduledEntries())

        self.assertEqual(expected, actual)

    def testTwoEntriesNextDate(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; yearly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.thingDate = date.today() - relativedelta(years=1)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(years=1)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)

    def testNoEntriesCount(self):
        testdate = LedgerThing.getDateString(
            date.today() + relativedelta(months=2)
        )
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)

        expected = 0
        actual = len(schedulething.getScheduledEntries())

        self.assertEqual(expected, actual)

    def testNoEntriesNextDate(self):
        testdate = LedgerThing.getDateString(
            date.today() + relativedelta(months=2)
        )
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(months=2)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)

    def testBimonthlyNextDate(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; bimonthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(months=2)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)

    def testQuarterlyNextDate(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; quarterly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(months=3)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)

    def testBiannualNextDate(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; biannual',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(months=6)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)

    def testYearlyNextDate(self):
        testdate = LedgerThing.getDateString(date.today())
        schedulelines = [
            '{date} lightning energy'.format(date=testdate),
            '    ;; schedule ; yearly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.getScheduledEntries()

        expected = date.today() + relativedelta(months=12)
        actual = schedulething.thingDate

        self.assertEqual(expected, actual)


class GetEntryThing(Redirector):

    def setUp(self):
        super(GetEntryThing, self).setUp()
        scheduleLineFileConfig = [
            ';; scheduler ; enter 7 days'
        ]
        ScheduleThing.doFileConfig = True
        ScheduleThing(scheduleLineFileConfig)

    def testBasicEntry(self):
        schedulelines = [
            '2013/06/13 lightning energy',
            '    ;; schedule ; monthly',
            '    blah blah blah',
        ]
        schedulething = ScheduleThing(schedulelines)
        schedulething.thingDate = date(2013, 07, 01)

        expected = [
            '2013/07/01 lightning energy',
            '    blah blah blah',
        ]

        actual = schedulething._getEntryThing().getLines()

        self.assertEqual(expected, actual)


class HandleThingConfig(Redirector):

    def setUp(self):
        super(HandleThingConfig, self).setUp()
        scheduleLineFileConfig = [
            ';; scheduler ; enter 7 days'
        ]
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
        # also tests sorting of days
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
        with self.assertRaises(LdgScheduleThingParametersError):
            ScheduleThing(schedulelines)

    def testScheduleLabelNotRight(self):
        schedulelines = [
            '2013/06/05 lightning energy',
            #'    ;; scheduled ; monthly ; eom30 2 15 ; 3 ; auto',
            '    ;; scheduble ; monthly',
        ]
        with self.assertRaises(LdgScheduleThingLabelError):
            ScheduleThing(schedulelines)

    def testScheduleUnrecognizedIntervalUOM(self):
        schedulelines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; lunarly ; eom30 2 15 ; every 3 months ; auto',
        ]
        with self.assertRaises(LdgScheduleUnrecognizedIntervalUom):
            ScheduleThing(schedulelines)

    def testIntervalEmpty(self):
        schedulelines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; monthly ; 15 eom30 ;   ; auto',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [15, 'eom30'], 1
            ),
            self.getActualConfig(schedulething)
        )

    def testIntervalNotGiven(self):
        schedulelines = [
            '2013/06/05 lightning energy',
            '    ;; schedule ; monthly ; 15 eom30',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [15, 'eom30'], 1
            ),
            self.getActualConfig(schedulething)
        )

    def testDaysEmpty(self):
        schedulelines = [
            '2013/06/27 lightning energy',
            '    ;; schedule ; monthly ;  ;  2 ',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [27], 2
            ),
            self.getActualConfig(schedulething)
        )

    def testNoDaysAndNoInterval(self):
        schedulelines = [
            '2013/06/13 lightning energy',
            '    ;; schedule ; monthly',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [13], 1
            ),
            self.getActualConfig(schedulething)
        )

    def testBimonthly(self):
        schedulelines = [
            '2013/06/13 lightning energy',
            '    ;; schedule ; bimonthly',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [13], 2
            ),
            self.getActualConfig(schedulething)
        )

    def testQuarterly(self):
        schedulelines = [
            '2013/06/13 lightning energy',
            '    ;; schedule ; quarterly ; 6th ; 3',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [6], 9
            ),
            self.getActualConfig(schedulething)
        )

    def testBiannual(self):
        schedulelines = [
            '2013/06/13 lightning energy',
            '    ;; schedule ; biannual ; 9th',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [9], 6
            ),
            self.getActualConfig(schedulething)
        )

    def testYearly(self):
        schedulelines = [
            '2013/06/22 lightning energy',
            '    ;; schedule ; yearly ; ; 5',
        ]
        schedulething = ScheduleThing(schedulelines)
        self.assertEqual(
            self.getExpectedConfig(
                ScheduleThing.INTERVAL_MONTH, [22], 60
            ),
            self.getActualConfig(schedulething)
        )


class HandleFileConfig(Redirector):

    def setUp(self):
        super(HandleFileConfig, self).setUp()
        ScheduleThing.doFileConfig = True
        ScheduleThing.enterDays = ScheduleThing.NO_DAYS
        ScheduleThing.entryBoundaryDate = None

    def getExpectedConfig(self, enterdays):
        return (
            '%s | %s' % (
                enterdays,
                LedgerThing.getDateString(
                    date.today() + relativedelta(days=enterdays)
                )
            )
        )

    def getActualConfig(self, schedulething):
        return (
            '%s | %s' % (
                schedulething.enterDays,
                LedgerThing.getDateString(
                    schedulething.entryBoundaryDate
                )
            )
        )

    def testBasicFileConfig(self):
        scheduleLineFileConfig = [
            ';; scheduler ; enter 7 days'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(7),
            self.getActualConfig(schedulething)
        )

    def testInvalidFileConfig(self):
        scheduleLineFileConfig = [
            ';; shceduler ; enter 7 days'
        ]
        with self.assertRaises(LdgScheduleFileConfigError):
            ScheduleThing(scheduleLineFileConfig)

    def testFileConfig(self):
        scheduleLineFileConfig = [
            ';;scheduler;enter 7 days;;'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(7),
            self.getActualConfig(schedulething)
        )

    def testFileConfigNoEnter(self):
        scheduleLineFileConfig = [
            ';;scheduler;;'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(ScheduleThing.NO_DAYS),
            self.getActualConfig(schedulething)
        )

    def testFileConfigEnterLessThanOne(self):
        scheduleLineFileConfig = [
            ';;   scheduler   ; enter 0 day ; comment'
        ]
        schedulething = ScheduleThing(scheduleLineFileConfig)
        self.assertEqual(
            self.getExpectedConfig(ScheduleThing.NO_DAYS),
            self.getActualConfig(schedulething)
        )


class GetNextDate(Redirector):

    def setUp(self):
        super(GetNextDate, self).setUp()
        scheduleLineFileConfig = [
            ';; scheduler ; enter 7 days'
        ]
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
            '    ;; schedule ; monthly ; 15th ; 3 ; auto',
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
            '    ;; schedule ; monthly ; eom ; 12 ; auto',
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
            '    ;; schedule ; monthly ; eom ; 12 ; auto',
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
            '    ;; schedule ; monthly ; 29th ; 1 ; auto',
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
            '    ;; schedule ; monthly ; 30th ; 1 ; auto',
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
            '    ;; schedule ; monthly ; 70th ; 1 ; auto',
        ]

        scheduleThing = ScheduleThing(scheduleLines)
        expectedNextDate = LedgerThing.getDate('2013/07/31')

        self.assertEqual(
            expectedNextDate,
            scheduleThing._getNextDate(scheduleThing.thingDate)
        )


class GetWeekDay(TestCase):

    def setUp(self):
        scheduleLinesTest = [
            '2013/06/29 lightning energy',
            '    ;; schedule ; monthly ; 12th ; ; auto'
        ]

        ScheduleThing.doFileConfig = False
        self.scheduleThing = ScheduleThing(scheduleLinesTest)

    def testGetWeekDay(self):
        self.assertEqual(-1, self.scheduleThing._getWeekDay())


class GetMonthDay(Redirector):

    def setUp(self):
        super(GetMonthDay, self).setUp()
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
