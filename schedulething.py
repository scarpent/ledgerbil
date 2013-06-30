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
    enterDays = -1
    previewDays = -1

    entryBoundaryDate = None
    previewBoundaryDate = None

    LINE_FILE_CONFIG = 0
    LINE_DATE = 0
    LINE_SCHEDULE = 1
    INTERVAL_WEEK = 'week'
    INTERVAL_MONTH = 'month'
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
    # enter and preview are both optional but if neither is included,
    # nothing will happen
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
            (?:\s*;\s*)?                        # optional ending semi-colon
            $                                   # line end
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

        self.isValidScheduleFile = True
        if match.group(ENTER_DAYS):
            ScheduleThing.enterDays = match.group(ENTER_DAYS)
            ScheduleThing.entryBoundaryDate = (
                date.today()
                + timedelta(days=int(ScheduleThing.enterDays))
            )
        if match.group(PREVIEW_DAYS):
            ScheduleThing.previewDays = match.group(PREVIEW_DAYS)

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
                self.interval = 1

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
                    self.days.append(int(match.groups()[0]))
                except:
                    self.days.append(match.groups()[0])
            self.days.sort()
            # todo: look for more than one eom and raise error?
            # raise error if no days?

        if not self.isScheduleThing:
            # todo: how to handle? stderr? exception? log? ignore?
            sys.stderr.write("it's not a schedule thing\n")

        # todo: take out schedule line and put it into var
        # override thing getter to put it back in (standard raw lines
        # will have it, but for adding to ledger, no

    def getScheduledEntries(self):

        entries = []

        # we want to include the date from the file as the next date, *if*
        # it's a valid schedule day, so we'll back up to give it a chance
        # to be discovered as the "nextDate"
        self.thingDate = self.thingDate - timedelta(days=1)

        while True:

            self.thingDate = self._getNextDate(self.thingDate)

            if self.thingDate > ScheduleThing.entryBoundaryDate:
                break

            entryLines = copy(self.lines)
            del entryLines[ScheduleThing.LINE_SCHEDULE]
            entryLines[ScheduleThing.LINE_DATE] = re.sub(
                self.DATE_REGEX,
                self.getDateString(self.thingDate),
                entryLines[ScheduleThing.LINE_DATE]
            )

            entries.append(LedgerThing(entryLines))

            print(
                '\n%s\n%s\n' % (
                    entryLines[ScheduleThing.LINE_DATE],
                    self.lines[ScheduleThing.LINE_SCHEDULE]
                    )
            )

        return entries


    def _getNextDate(self, currentdate):
        """
        @type currentdate: date
        """
        if self.intervalUom == ScheduleThing.INTERVAL_MONTH:
            # add day so we can compare with >=
            # also assures that we always get a future date
            currentdate = currentdate + timedelta(days=1)
            # first see if more days to go in the current month
            # advance month at end of loop
            while True:
                for scheduleday in self.days:
                    scheduleday = self._getMonthDay(scheduleday, currentdate)
                    if scheduleday >= currentdate.day:
                        return date(
                            currentdate.year,
                            currentdate.month,
                            scheduleday)

                currentdate = date(
                    currentdate.year,
                    currentdate.month,
                    1) + relativedelta(months=self.interval)

        # todo:
        sys.stderr.write('\nunhandled interval uom; advancing scheduled date past entry boundery date\n')
        return ScheduleThing.entryBoundaryDate + timedelta(days=1)


    # knows how to handle "eom"
    def _getMonthDay(self, scheduleday, currentdate):
        """
        @type scheduleday: str
        @type currentdate: date
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
