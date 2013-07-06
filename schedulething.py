#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
import re
from copy import copy
from datetime import date
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange

from ledgerthing import LedgerThing


class ScheduleThing(LedgerThing):

    doFileConfig = True

    NO_DAYS = 0
    enterDays = NO_DAYS
    previewDays = NO_DAYS

    entryBoundaryDate = None
    previewBoundaryDate = None

    LINE_FILE_CONFIG = 0
    LINE_DATE = 0
    LINE_SCHEDULE = 1
    INTERVAL_WEEK = 'week'
    INTERVAL_MONTH = 'month'
    INTERVAL_BIMONTHLY = 'bimonthly'
    INTERVAL_QUARTER = 'quarter'
    INTERVAL_YEAR = 'year'
    # one time schedule
    EOM = 'eom'
    EOM30 = 'eom30'

    def __init__(self, lines):
        self.firstThing = False
        self.isScheduleThing = False
        self.intervalUom = ''           # e.g. month, week
        self.days = []                  # e.g. 5, 15, eom, eom30
        self.interval = 1               # e.g. 1 = every month, 2 = every other
        self.previewDate = None

        super(ScheduleThing, self).__init__(lines)

        if ScheduleThing.doFileConfig:
            self._handleFileConfig(lines[ScheduleThing.LINE_FILE_CONFIG])
            self.firstThing = True
            ScheduleThing.doFileConfig = False
            return

        self._handleThingConfig(lines[ScheduleThing.LINE_SCHEDULE])

    # file level config looks like this:
    # ;; scheduler ; enter N days ; preview N days
    # enter and preview are both optional
    def _handleFileConfig(self, line):

        configRegex = r'''(?x)                  # verbose mode
            ^                                   # line start
            \s*;;\s*scheduler\s*                # required
            (?:                                 # non-capturing
                ;\s*enter\s+(\d+)\s+days?\s*    # days ahead to enter trans
            )?                                  # optional
            (?:                                 # non-capturing
                ;\s*preview\s+(\d+)\s+days?\s*  # days to "preview" trans
            )?                                  # optional
            (?:\s*;.*)?                         # optional ending semi-colon
            $                                   # line end     \ and comment
            '''

        # capturing groups
        ENTER_DAYS = 1
        PREVIEW_DAYS = 2

        match = re.match(configRegex, line)
        if not match:
            raise Exception(
                'Invalid schedule file config:\n%s\nExpected:\n'
                ';; scheduler ; enter N days ; preview N days'
                % line
            )

        if match.group(ENTER_DAYS):
            ScheduleThing.enterDays = int(match.group(ENTER_DAYS))

            if ScheduleThing.enterDays < 1:
                ScheduleThing.enterDays = ScheduleThing.NO_DAYS

        ScheduleThing.entryBoundaryDate = (
            date.today()
            + timedelta(days=ScheduleThing.enterDays)
        )
        if match.group(PREVIEW_DAYS):
            ScheduleThing.previewDays = int(match.group(PREVIEW_DAYS))

            if ScheduleThing.previewDays <= ScheduleThing.enterDays:
                ScheduleThing.previewDays = ScheduleThing.NO_DAYS

        ScheduleThing.previewBoundaryDate = (
            date.today()
            + timedelta(days=ScheduleThing.previewDays)
        )

        print('\nSchedule file (enter days = %s, preview days = %s):\n'
              % (ScheduleThing.enterDays, ScheduleThing.previewDays))

    def _handleThingConfig(self, line):

        thingRegex = r'''(?xi)          # verbose mode, ignore case
            ^                           # line start
            \s*;;\s*schedule\s*         # required
            ;\s*(week|month)(?:ly)?\s*  # interval uom
            ;\s*([^;]+?)\s*             # days (to be parsed further)
            (?:;[^;\d]*(\d+)[^;]*)?     # optional interval (default = 1)
            (?:;.*)?                    # non-capturing, optional comment
            (?:;\s*|$)                  # line end
            '''

        # capturing groups
        INTERVAL_UOM = 1
        DAYS = 2
        INTERVAL = 3

        match = re.match(thingRegex, line)
        if match:
            self.intervalUom = match.group(INTERVAL_UOM).lower()
            try:
                self.interval = int(match.group(INTERVAL))
            except:
                self.interval = 1

            if self.interval < 1:
                self.interval = 1  # interval must not be less than one

            # todo: translate "yearly" into month uom and every 12 months

            # for monthly: the day date; for weekly: the day name
            # todo: parse that as day names, but for now, use ints
            # todo: if days not specified, default to thing day
            # (if day < 1, consider an inactive thing)
            dayString = match.group(DAYS).lower()
            self.days = []
            daysRegex = '(\d+|eom(?:\d+)?)'
            for match in re.finditer(daysRegex, dayString):
                self.isScheduleThing = True
                # convert to ints where possible so will sort out correctly
                try:
                    theday = int(match.groups()[0])

                    if theday == 29 or theday == 30:
                        sys.stderr.write(
                            'Using eom30 for schedule day %s\n' % theday
                        )
                        theday = ScheduleThing.EOM30
                    elif theday > 30:
                        sys.stderr.write(
                            'Using eom for schedule day %s\n' % theday
                        )
                        theday = ScheduleThing.EOM
                except:
                    theday = match.groups()[0]

                self.days.append(theday)

            self.days.sort()
            # todo: look for more than one eom and raise error?
            # todo: if no days, use day of thing date
            # todo: validation if a date is picked that is too
            #       large for some months (maybe force eom for 28-31???

        if not self.isScheduleThing:
            # todo: how to handle? stderr? exception? log? ignore?
            sys.stderr.write("it's not a schedule thing\n")

        # todo: take out schedule line and put it into var
        # override thing getter to put it back in (standard raw lines
        # will have it, but for adding to ledger, no

    def getScheduledEntries(self):

        entries = []

        if self.thingDate <= ScheduleThing.entryBoundaryDate:
            entries.append(self._getEntryThing())

        while True:
            self.thingDate = self._getNextDate(self.thingDate)

            if self.thingDate > ScheduleThing.entryBoundaryDate:
                break

            entries.append(self._getEntryThing())

        return entries

    def _getEntryThing(self):
        """
        @rtype: LedgerThing
        """
        entryLines = copy(self.lines)
        del entryLines[ScheduleThing.LINE_SCHEDULE]
        entryLines[ScheduleThing.LINE_DATE] = re.sub(
            self.DATE_REGEX,
            self.getDateString(self.thingDate),
            entryLines[ScheduleThing.LINE_DATE]
        )
        print(
            '\n%s\n%s\n' % (
                entryLines[ScheduleThing.LINE_DATE],
                self.lines[ScheduleThing.LINE_SCHEDULE]
            )
        )
        return LedgerThing(entryLines)

    def _getNextDate(self, previousdate):
        """
        @type previousdate: date
        @rtype: date
        """
        if self.intervalUom == ScheduleThing.INTERVAL_MONTH:

            # first see if any scheduled days remaining in same month
            for scheduleday in self.days:
                scheduleday = self._getMonthDay(scheduleday, previousdate)
                # compare with greater so we don't keep matching the same
                if scheduleday > previousdate.day:
                    return date(
                        previousdate.year,
                        previousdate.month,
                        scheduleday)

            # advance to next month (by specified interval)

            nextmonth = previousdate + relativedelta(months=self.interval)

            return date(
                nextmonth.year,
                nextmonth.month,
                self._getMonthDay(self.days[0], nextmonth)
            )

        # todo: maybe can assume is valid if thing initialized successfully
        sys.stderr.write('\nunhandled interval uom; advancing scheduled date past entry boundary date\n')
        return ScheduleThing.entryBoundaryDate + timedelta(days=1)


    # knows how to handle "eom"
    def _getMonthDay(self, scheduleday, currentdate):
        """
        @type scheduleday: str
        @type currentdate: date
        @rtype: int
        """
        if str(scheduleday).isdigit():
            return int(scheduleday)

        lastDayOfMonth = monthrange(currentdate.year, currentdate.month)[1]

        # todo, maybe: option to move date if a weekend

        if scheduleday == self.EOM:
            return lastDayOfMonth

        if scheduleday == '%s%s' % (self.EOM, '30'):
            if lastDayOfMonth >= 30:
                return 30
            else:
                return lastDayOfMonth # february

    def _getWeekDay(self):
        return -1
