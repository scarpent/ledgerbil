#!/usr/bin/python

"""schedule file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import re

from ledgerfile import LedgerFile
from schedulething import ScheduleThing


class ScheduleFile(LedgerFile):

    daysAheadRegex = r'''(?x)               # verbose mode
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

    def __init__(self, filename):
        self.enterDays = -1
        self.previewDays = -1

        super(ScheduleFile, self).__init__(filename)

        print('\nSchedule file (enter days = %s, preview days = %s):\n'
              % (self.enterDays, self.previewDays))
        self.printFile()

    def _addThingLines(self, lines):
        if lines:
            thing = ScheduleThing(lines)
            self.addThing(thing)

    def addThing(self, thing):
        super(ScheduleFile, self).addThing(thing)
        if thing.thingNumber == 0:
            self.handleFirstThing()
        else:
            self.handleSubsequentThings(thing.thingNumber)

    # start out by requiring that the ";; scheduler" line is first in file
    def handleFirstThing(self):
        ENTER_DAYS = 1
        PREVIEW_DAYS = 2
        firstline = self.getThings()[0].getLines()[0]

        match = re.match(self.daysAheadRegex, firstline)
        if match:
            if match.group(ENTER_DAYS):
                self.enterDays = match.group(ENTER_DAYS)
            if match.group(PREVIEW_DAYS):
                self.previewDays = match.group(PREVIEW_DAYS)
        else:
            raise Exception(
                '%s is not a valid schedule file - \n'
                'first line must have scheduler directive, e.g.:\n'
                ';; scheduler ; enter 7 days ; preview 30 days'
                % self.filename
            )

    def handleSubsequentThings(self, thingNumber):
        print ('this is thing %s' % (self.getThings()[thingNumber].thingNumber + 1))
