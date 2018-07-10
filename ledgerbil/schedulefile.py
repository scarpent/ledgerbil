from .ledgerfile import LedgerFile
from .schedulething import ScheduleThing


class ScheduleFile(LedgerFile):

    def __init__(self, filename):
        ScheduleThing.do_file_config = True
        ScheduleThing.enter_days = 0
        ScheduleThing.entry_boundary_date = None
        super().__init__(filename, reconcile_account=None)

    def _add_thing_from_lines(self, lines):
        if lines:
            thing = ScheduleThing(lines)
            self.add_thing(thing)

    def next_scheduled_date(self):
        self.sort()
        for thing in self.get_things():
            if thing.is_transaction:
                return thing.get_date_string()

        return ''
