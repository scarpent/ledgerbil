import sys
from datetime import date
from operator import attrgetter

from .ledgerthing import LedgerThing
from .util import assert_only_one_matching_account


class LedgerFile:
    STARTING_DATE = date(1899, 1, 1)
    thing_counter = -1

    def __init__(self, filename, reconcile_account=None):
        self.filename = filename
        self.rec_account = reconcile_account  # could be partial
        self.reset()

    def reset(self):
        self.things = []
        self.rec_account_matched = None  # full account name
        self.read_file()

    def read_file(self):
        if not self.is_writable():
            sys.exit(-1)

        current_lines = []
        with open(self.filename, 'r', encoding='utf-8') as the_file:
            for line in the_file:
                line = line.rstrip()
                if LedgerThing.is_new_thing(line):
                    self.add_thing_from_lines(current_lines)
                    current_lines = []

                current_lines.append(line)

        self.add_thing_from_lines(current_lines)

    def is_writable(self):
        # This will catch read-only files as well as bad filenames
        try:
            with open(self.filename, 'r+'):
                return True
        except IOError as e:
            print(f'error: {e}', file=sys.stderr)
            return False

    def add_thing_from_lines(self, lines):
        lines = remove_trailing_blank_lines(lines)
        if lines:
            thing = LedgerThing(lines, self.rec_account)
            self.add_thing(thing)

    def add_thing(self, thing):
        things = [thing]
        self.add_things(things)

    def add_things(self, things):
        for thing in things:
            if self.rec_account and thing.rec_account_matched:
                if not self.rec_account_matched:
                    self.rec_account_matched = thing.rec_account_matched
                else:
                    assert_only_one_matching_account({
                        self.rec_account_matched,
                        thing.rec_account_matched,
                    })

            thing.thing_number = LedgerFile.next_thing_number()
            self.things.append(thing)

    @staticmethod
    def next_thing_number():
        LedgerFile.thing_counter += 1
        return LedgerFile.thing_counter

    def sort(self):
        current_date = self.STARTING_DATE

        for thing in self.things:
            if thing.thing_date is None:
                thing.thing_date = current_date
            else:
                current_date = thing.thing_date

        self.things.sort(key=attrgetter('thing_date', 'thing_number'))

    def print_file(self):
        for thing in self.things:
            for line in thing.get_lines():
                print(line)
            print()

    def write_file(self):
        with open(self.filename, 'w', encoding='utf-8') as the_file:
            for thing in self.things:
                the_file.write('\n'.join(thing.get_lines()) + '\n\n')


def remove_trailing_blank_lines(lines):
    for line in reversed(lines):
        if line == '':
            lines.pop()
        else:
            break

    return lines
