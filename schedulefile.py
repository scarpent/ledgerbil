#!/usr/bin/python

"""schedule file"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from ledgerfile import LedgerFile
from schedulething import ScheduleThing


class ScheduleFile(LedgerFile):

    # def __init__(self, filename):
    #     super(ScheduleFile, self).__init__(filename)
    #
    #     print('\nSchedule file (enter days = %s, preview days = %s):\n'
    #           % (ScheduleThing.enterDays, ScheduleThing.previewDays))
    #     self.printFile()

    def _addThingLines(self, lines):
        if lines:
            thing = ScheduleThing(lines)
            self.addThing(thing)

    def run(self, ledgerFile):
        for thing in self.things:

            if not thing.isScheduleThing:
                print('not a thing...')  # todo: temp for dev/debug
                continue

            print('a thing! date = %s' % thing.date)
            print('\tdays = %s, interval = %s, uom = %s'
                  % (thing.days, thing.interval, thing.intervalUom))
            print('adding it to ledger file')

            # temp -- will have better ways to remove this
            del thing.lines[1]

            ledgerFile.addThing(thing)


