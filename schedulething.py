#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
import re
from copy import copy
from datetime import datetime
from datetime import timedelta

from ledgerthing import LedgerThing


class ScheduleThing(LedgerThing):

    firstThing = True
    enterDays = -1
    previewDays = -1

    entryBoundaryDate = None
    previewBoundaryDate = None

    def __init__(self, lines):
        self.isScheduleThing = False
        self.intervalUom = ''           # e.g. month, week
        self.days = ()                  # e.g. 5, 15, eom, eom30
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

        ScheduleThing.isValidScheduleFile = True
        if match.group(ENTER_DAYS):
            ScheduleThing.enterDays = match.group(ENTER_DAYS)
            ScheduleThing.entryBoundaryDate = (
                datetime.today()
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
        INTERVAL = 1
        DAYS = 2
        INTERVAL_UOM = 3

        match = re.match(thingRegex, line)
        if match:
            self.interval = match.group(INTERVAL).lower()
            self.intervalUom = match.group(INTERVAL_UOM)
            if self.intervalUom is None:
                self.intervalUom = 1

            # for monthly: the day date; for weekly: the day name
            # todo: parse that as day names, but for now, use ints
            dayString = match.group(DAYS)
            self.days = []
            daysRegex = '(\d+|eom(?:\d+)?)'
            for match in re.finditer(daysRegex, dayString):
                self.isScheduleThing = True
                self.days.append(match.groups()[0])

            # todo: look for more than one eom and raise error?

        if not self.isScheduleThing:
            # todo: how to handle? stderr? exception? log? ignore?
            sys.stderr.write("it's not a schedule thing\n")

        # todo: take out schedule line and put it into var
        # override thing getter to put it back in (standard raw lines
        # will have it, but for adding to ledger, no

    def getScheduledEntries(self):
        entryLines = copy(self.lines)

        entries =[]

        entryLines[0] = re.sub(self.dateRegex, self.date, entryLines[0])
        del entryLines[1]

        scheduleDate = datetime.strptime(self.date, '%Y/%m/%d')

        if scheduleDate <= self.entryBoundaryDate:
            entries.append(LedgerThing(entryLines))
            # advance date

        return entries
