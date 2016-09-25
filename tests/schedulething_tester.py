#!/usr/bin/python

"""initializes ScheduleThing class for testing"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from unittest import TestCase

from redirector import Redirector
from schedulething import ScheduleThing


class ScheduleThingTester(Redirector):

    def setUp(self):
        super(ScheduleThingTester, self).setUp()
        ScheduleThing.doFileConfig = True
        ScheduleThing.enterDays = ScheduleThing.NO_DAYS
        ScheduleThing.previewDays = ScheduleThing.NO_DAYS
        ScheduleThing.entryBoundaryDate = None
        ScheduleThing.previewBoundaryDate = None

