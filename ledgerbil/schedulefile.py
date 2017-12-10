from .ledgerfile import LedgerFile
from .schedulething import ScheduleThing


class ScheduleFile(LedgerFile):

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
