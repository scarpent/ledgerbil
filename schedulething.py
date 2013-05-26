#!/usr/bin/python

"""objects in ledger file: transactions, etc"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


import re

from ledgerthing import LedgerThing


class ScheduleThing(LedgerThing):

    firstThing = True
    enterDays = -1
    previewDays = -1

    # individual schedule items (second line of thing)
    scheduleThingRegex = r'\s*;;\s*schedule\s*'

    def __init__(self, lines):
        self.isAScheduleThing = False
        self.interval = -1
        self.intervalUom = ''

        super(ScheduleThing, self).__init__(lines)

        if ScheduleThing.firstThing:
            self.handleFileConfig(lines[0])
            ScheduleThing.firstThing = False
            return

        # todo: test single line thing? although would be invalid thing
        self.handleThingConfig(lines[1])

    def handleFileConfig(self, line):

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
        if match.group(PREVIEW_DAYS):
            ScheduleThing.previewDays = match.group(PREVIEW_DAYS)

    def handleThingConfig(self, line):

        thingRegex = r'''(?x)                   # verbose mode
            ^                                   # line start
            \s*;;\s*schedule\s*                                  # required
            ;\s*every\s+                        #
            (\d+)                               # interval (e.g. 1)
            \s+                                 #
            (\S+)                               # interval uom (e.g. month)
            \s*                                 #
            (?:                                 # non-capturing
                .*                              # optional whatever
            )                                   #
            $                                   # line end
            '''

        INTERVAL = 1
        INTERVAL_UOM = 2

        match = re.match(thingRegex, line)
        if match:
            self.isAScheduleThing = True
            self.interval = match.group(INTERVAL)
            self.intervalUom = match.group(INTERVAL_UOM)

            print("it's a thing: interval = %s, uom = %s"
                  % (self.interval, self.intervalUom))
        else:
            # todo: how to handle "not things"? stderr? exception? log?
            print("it's not a thing")
