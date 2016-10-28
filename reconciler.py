#!/usr/bin/env python

from __future__ import division
from __future__ import print_function

import cmd

from datetime import date

import util

__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class Reconciler(cmd.Cmd, object):

    UNKNOWN_SYNTAX = '*** Unknown syntax: '
    NO_HELP = '*** No help on '

    def __init__(self, ledgerfile):
        cmd.Cmd.__init__(self)
        self.aliases = {
            'end': self.do_finish,
            'EOF': self.do_quit,
            'l': self.do_list,
            'll': self.do_list,
            'm': self.do_mark,
            'u': self.do_unmark,
            'un': self.do_unmark,
            'q': self.do_quit,
            'start': self.do_statement,
        }

        self.ledgerfile = ledgerfile
        self.to_date = date.today()
        self.ending_balance = None
        self.open_transactions = []
        self.current_listing = {}
        self.total_cleared = 0
        self.total_pending = 0

        self.populate_open_transactions()

    intro = ''
    prompt = '> '

    def emptyline(self):
        pass  # pragma: no cover

    def default(self, line):
        command, arg, line = self.parseline(line)

        if command == 'EOF':
            print()

        if command in self.aliases:
            return self.aliases[command](arg)
        elif util.is_integer(line):
            return self.do_mark(line)
        else:
            print(self.UNKNOWN_SYNTAX + line)

    def do_help(self, arg):
        """Get help for a command; Syntax: help <COMMAND>"""
        if arg in self.aliases:
            arg = self.aliases[arg].__name__[3:]
        cmd.Cmd.do_help(self, arg)

    def do_aliases(self, arg):
        """Print aliases"""
        for alias in sorted(
                self.aliases.keys(),
                key=lambda x: x.lower()
        ):
            print('{alias:5}{command}'.format(
                alias=alias,
                command=self.aliases[alias].__name__[3:]
            ))

    def do_quit(self, arg):
        """Exit the program"""
        return True

    def do_list(self, args):
        """List entries for selected account

        - Shows uncleared and pending transactions (Pending = "!")
        """
        self.list_transactions()

    def do_account(self, args):
        """Print the account being reconciled"""
        print(self.ledgerfile.rec_account_matches[0])

    def do_mark(self, args):
        """Mark a transaction as pending (!)

        Syntax: mark <#> or <# ... #>
                <#>

        - The numbered line of a transaction, or multiple numbers
          separated by spaces
        - Without "mark", a single transaction number
        """
        self.mark_or_unmark(args, mark=True)

    def do_unmark(self, args):
        """Remove pending mark (!) from transaction

        Syntax: unmark <#>

        - The numbered line of a transaction, or multiple numbers
          separated by spaces
        """
        self.mark_or_unmark(args, mark=False)

    def do_statement(self, args):
        """Set or adjust statement date and ending balance"""
        self.set_statement_info()

    def do_finish(self, args):
        """Finish balancing the account

        - Marking all pending transactions as cleared (*) if the ending
          balance is set and the total is zeroed out
       """
        self.finish_balancing()

    def populate_open_transactions(self):
        self.open_transactions = []
        self.current_listing = {}
        self.total_cleared = 0
        self.total_pending = 0

        for thing in self.ledgerfile.get_things():
            if thing.rec_account_matches:
                if thing.is_cleared():
                    self.total_cleared += thing.rec_amount
                    continue

                if thing.is_pending():
                    self.total_pending += thing.rec_amount

                self.open_transactions.append(thing)

        self.do_list('')

    def mark_or_unmark(self, args, mark=True):
        args = util.parse_args(args)
        if not args:
            print('*** Transaction number(s) required')
            return

        at_least_one_success = False
        messages = ''
        for num in args:
            if num not in self.current_listing:
                messages += 'Transaction not found: {}\n'.format(num)
                continue

            thing = self.current_listing[num]

            if mark and thing.is_pending():
                messages += 'Already marked pending: ' + num + '\n'
                continue
            elif not mark and not thing.is_pending():
                messages += "Not marked; can't unmark: " + num + '\n'
                continue

            if mark:
                self.current_listing[num].set_pending()
                self.total_pending += thing.rec_amount
            else:
                thing.set_uncleared()
                self.total_pending -= thing.rec_amount

            self.ledgerfile.write_file()
            at_least_one_success = True

        if at_least_one_success:
            self.list_transactions()

        if messages:
            print(messages, end='')

    def list_transactions(self):
        self.current_listing = {}
        count = 0
        for thing in self.open_transactions:
            if thing.thing_date > self.to_date \
                    and not thing.is_pending():
                continue

            if not self.current_listing:
                print()  # only print one buffer line at top if items

            count += 1
            self.current_listing[str(count)] = thing
            count_str = '{:-4}.'.format(count)
            print(
                '{number} {date} {amount} {status:1} {payee} '
                '{code:>7}'.format(
                    number=util.get_cyan_text(count_str),
                    date=thing.get_date_string(),
                    code=thing.transaction_code,
                    payee=util.get_cyan_text(
                        thing.payee,
                        column_width=40
                    ),
                    amount=util.get_colored_amount(
                        thing.rec_amount,
                        10
                    ),
                    status=thing.rec_status
                )
            )

        end_date = util.get_cyan_text(
            util.get_date_string(self.to_date)
        )

        if self.ending_balance is None:
            end_balance = util.get_cyan_text('(not set)')
        else:
            end_balance = util.get_colored_amount(self.ending_balance)

        print(
            '\nending date: {end_date} ending balance: {end_balance} '
            'cleared: {cleared}'.format(
                end_date=end_date,
                end_balance=end_balance,
                cleared=util.get_colored_amount(self.total_cleared)
        ))

        if self.ending_balance is not None:
            print('to zero: {}'.format(
                util.get_colored_amount(self.get_zero_candidate())
            ))

        print()

    def set_statement_info(self):
        old_ending_date = self.to_date
        while True:
            date_str = util.get_date_string(self.to_date)
            new_date = self.get_response(
                prompt='Ending Date (YYYY/MM/DD)',
                old_value=date_str
            )
            try:
                self.to_date = util.get_date(new_date)
                break
            except ValueError:
                print('*** Invalid date')

        new_ending_balance = None
        if self.ending_balance is None:
            old_ending_balance = None
        else:
            old_ending_balance = util.get_amount_str(
                self.ending_balance
            )

        while True:
            new_ending_balance = self.get_response(
                prompt='Ending Balance',
                old_value=old_ending_balance
            )
            if new_ending_balance is None:
                break

            try:
                self.ending_balance = float(
                    new_ending_balance.replace('$', '')
                )
                break
            except ValueError:
                print('*** Invalid number')

        if new_ending_balance is not None:
            new_ending_balance = util.get_amount_str(
                self.ending_balance
            )

        if old_ending_date != self.to_date \
                or old_ending_balance != new_ending_balance:
            self.list_transactions()

    def finish_balancing(self):

        if self.ending_balance is None:
            print('*** Ending balance must be set in order to finish')
            return

        if util.get_amount_str(self.get_zero_candidate()) == '$0.00':
            print('"To zero" must be zero in order to finish')
            return

        for thing in self.open_transactions:
            if thing.is_pending():
                thing.set_cleared()

        self.ending_balance = None
        self.ledgerfile.write_file()

        self.populate_open_transactions()

    def get_zero_candidate(self):
        return (
            self.ending_balance
            - (self.total_cleared + self.total_pending)
        )

    # noinspection PyCompatibility
    @staticmethod
    def get_response(prompt='', old_value=''):
        default = '' if old_value is None else old_value
        response = raw_input('{prompt} [{default}]: '.format(
            prompt=prompt,
            default=default
        )).strip()

        if response == '':
            response = old_value

        return response
