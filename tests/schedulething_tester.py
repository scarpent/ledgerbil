#!/usr/bin/python

"""initializes ScheduleThing class for testing"""

from redirector import Redirector
from schedulething import ScheduleThing


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class ScheduleThingTester(Redirector):

    def setUp(self):
        super(ScheduleThingTester, self).setUp()
        ScheduleThing.doFileConfig = True
        ScheduleThing.enterDays = ScheduleThing.NO_DAYS
        ScheduleThing.entryBoundaryDate = None
