#!/usr/bin/env python

"""ledger file base class"""

from __future__ import print_function

import sys

from datetime import date
from operator import attrgetter

from ledgerbilexceptions import LdgReconcilerMoreThanOneMatchingAccount
from ledgerthing import LedgerThing


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class LedgerFile(object):

    STARTING_DATE = date(1899, 1, 1)

    def __init__(self, filename, reconcile_account=None):
        self.thing_counter = 0
        self.things = []
        self.filename = filename
        self.rec_account = reconcile_account  # could be partial
        self.rec_account_matches = []  # should be only one match

        self._read_file()

    def _read_file(self):
        self._test_writable()  # want to make sure we can later write
        current_lines = []
        with open(self.filename, 'r') as the_file:
            for line in the_file:
                line = line.rstrip()
                if LedgerThing.is_new_thing(line):
                    self._add_thing_lines(current_lines)
                    current_lines = []

                current_lines.append(line)

        self._add_thing_lines(current_lines)

    def _test_writable(self):
        try:
            with open(self.filename, 'r+'):
                pass
        except IOError as e:
            sys.stderr.write('error: %s\n' % e)
            sys.exit(-1)

    @staticmethod
    def _remove_trailing_blank_lines(lines):
        if not lines:
            return lines

        for line in reversed(lines):
            if line == '':
                lines.pop()
            else:
                break

        return lines

    def _add_thing_lines(self, lines):
        lines = self._remove_trailing_blank_lines(lines)
        if lines:
            thing = LedgerThing(lines, self.rec_account)
            self.add_thing(thing)

    def add_thing(self, thing):
        things = [thing]
        self.add_things(things)

    def add_things(self, things):
        for thing in things:

            if self.rec_account and len(thing.rec_account_matches) > 0:
                assert len(thing.rec_account_matches) == 1
                thing_account = thing.rec_account_matches[0]
                if thing_account not in self.rec_account_matches:
                    self.rec_account_matches.append(thing_account)

                # unlike LedgerThing multiple match checking, we'll
                # raise this one right away, since we don't know how
                # many things are still to be added, if any
                if len(self.rec_account_matches) > 1:
                    raise LdgReconcilerMoreThanOneMatchingAccount(
                        self.rec_account_matches
                    )

            thing.thing_number = self.thing_counter
            self.get_things().append(thing)
            # increment after for a zero-based array
            self.thing_counter += 1

    def get_things(self):
        return self.things

    def sort(self):
        current_date = self.STARTING_DATE

        for thing in self.get_things():
            if thing.thing_date is None:
                thing.thing_date = current_date
            else:
                current_date = thing.thing_date

        self.get_things().sort(
            key=attrgetter('thing_date', 'thing_number')
        )

    def print_file(self):
        for thing in self.get_things():
            for line in thing.get_lines():
                print(line)
            print()

    def write_file(self):
        with open(self.filename, 'w') as the_file:
            for thing in self.get_things():
                for line in thing.get_lines():
                    the_file.write(line + '\n')
                the_file.write('\n')

    def get_reconciliation_account(self):
        if len(self.rec_account_matches) == 1:
            return self.rec_account_matches[0]
        else:
            return None
