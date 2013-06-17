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

    firstThing = True
    enterDays = -1
    previewDays = -1

    entryBoundaryDate = None
    previewBoundaryDate = None

    INTERVAL_MONTH = 'month'
    INTERVAL_WEEK = 'week'
    EOM = 'eom'
    EOM30 = 'eom30'

    def __init__(self, lines):
        self.isScheduleThing = False
        self.intervalUom = ''           # e.g. month, week
        self.days = []                  # e.g. 5, 15, eom, eom30
        self.interval = 1               # e.g. 1 = every month, 2 = every other
        self.previewDate = None

        super(ScheduleThing, self).__init__(lines)

        if ScheduleThing.firstThing:
            self._handleFileConfig(lines[0])
            ScheduleThing.firstThing = False
            return

        # todo: test single line thing? although would be invalid thing
        self._handleThingConfig(lines[1])

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
            ;\s*([^;]+?)\s*             # days (to be parsed further, later)
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
            self.interval = match.group(INTERVAL)
            if self.interval is None or self.interval < 1:
                self.interval = 1

            # for monthly: the day date; for weekly: the day name
            # todo: parse that as day names, but for now, use ints
            dayString = match.group(DAYS).lower()
            self.days = []
            daysRegex = '(\d+|eom(?:\d+)?)'
            for match in re.finditer(daysRegex, dayString):
                self.isScheduleThing = True
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

        while self.thingDate <= ScheduleThing.entryBoundaryDate:

            entryLines = copy(self.lines)
            del entryLines[1]
            entryLines[0] = re.sub(
                self.DATE_REGEX,
                self.getDateString(self.thingDate),
                entryLines[0]
            )

            entries.append(LedgerThing(entryLines))
            nextDate = self.getNextDate(self.thingDate)

            # with proper programming of getNextDate, this shouldn't
            #  happen, but we'll over-cautiously avoid infinite loop
            if nextDate <= self.thingDate:
                break

            self.thingDate = nextDate



        return entries


    def getNextDate(self, currentdate):
        """
        @type currentdate: date
        """
        if self.intervalUom == self.INTERVAL_MONTH:
            # first see if more days to go in the current month
            for scheduleday in self.days:
                scheduleday = self.getMonthDay(scheduleday, currentdate)
                if scheduleday > currentdate.day:
                    return date(
                        currentdate.year,
                        currentdate.month,
                        scheduleday)

        return currentdate


    # knows how to handle "eom"
    def getMonthDay(self, scheduleday, currentdate):
        """
        @type scheduleday: str
        @type currentdate: date
        """
        if scheduleday.isdigit():
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

    def getWeekDay(self):
        pass
