#!/usr/bin/python

"""initializes ScheduleThing class for testing"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from unittest import TestCase
from schedulething import ScheduleThing

class ScheduleThingTester(TestCase):

    def setUp(self):
        ScheduleThing.doFileConfig = True
        ScheduleThing.enterDays = ScheduleThing.NO_DAYS
        ScheduleThing.previewDays = ScheduleThing.NO_DAYS
        ScheduleThing.entryBoundaryDate = None
        ScheduleThing.previewBoundaryDate = None

