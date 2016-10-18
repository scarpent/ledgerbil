#!/usr/bin/python

"""schedule file"""

from __future__ import print_function

__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from ledgerfile import LedgerFile
from schedulething import ScheduleThing


class ScheduleFile(LedgerFile):

    def _addThingLines(self, lines):
        if lines:
            thing = ScheduleThing(lines)
            self.addThing(thing)
