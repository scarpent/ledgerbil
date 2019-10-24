from .ledgerfile import LedgerFile, remove_trailing_blank_lines
from .schedulething import ScheduleThing


class ScheduleFile(LedgerFile):
    def __init__(self, filename):
        ScheduleThing.do_file_config = True
        ScheduleThing.enter_days = 0
        ScheduleThing.entry_boundary_date = None
        super().__init__(filename, reconcile_account=None)

    def add_thing_from_lines(self, lines):
        lines = remove_trailing_blank_lines(lines)
        if lines:
            thing = ScheduleThing(lines)
            self.add_things([thing])

    def next_scheduled_date(self):
        self.sort()
        for thing in self.things:
            if thing.is_transaction:
                return thing.get_date_string()

        return ""
