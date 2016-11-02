"""initializes ScheduleThing class for testing"""

from helpers import Redirector
from schedulething import ScheduleThing


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class ScheduleThingTester(Redirector):

    def setUp(self):
        super(ScheduleThingTester, self).setUp()
        ScheduleThing.do_file_config = True
        ScheduleThing.enter_days = ScheduleThing.NO_DAYS
        ScheduleThing.entry_boundary_date = None
