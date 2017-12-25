"""initializes ScheduleThing class for testing"""

from ..schedulething import ScheduleThing
from .helpers import Redirector


class ScheduleThingTester(Redirector):

    def setUp(self):
        super(ScheduleThingTester, self).setUp()
        ScheduleThing.do_file_config = True
        ScheduleThing.enter_days = ScheduleThing.NO_DAYS
        ScheduleThing.entry_boundary_date = None
