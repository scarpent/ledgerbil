#!/usr/bin/env python

from __future__ import division
from __future__ import print_function

import cmd

import util

from datetime import date
from dateutil.relativedelta import relativedelta


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


# noinspection PyMethodMayBeStatic
class Reconciler(cmd.Cmd, object):

    UNKNOWN_SYNTAX = '*** Unknown syntax: '
    NO_HELP = '*** No help on '

    def __init__(self, ledgerfile, account):
        cmd.Cmd.__init__(self)
        self.aliases = {
            'EOF': self.do_quit,
            'l': self.do_list,
            'll': self.do_list,
            'q': self.do_quit,
        }

        self.ledgerfile = ledgerfile
        self.account = account

        self.list_cleared = False
        self.list_future = False

    intro = ''
    prompt = 'rec: '

    def emptyline(self):
        pass  # pragma: no cover

    def default(self, line):
        command, arg, line = self.parseline(line)

        if command == 'EOF':
            print()

        if command in self.aliases:
            return self.aliases[command](arg)
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

        Syntax: list [+/-cleared] [+/-future]
                list [future] [cleared]

        - "+cleared" will show cleared entries; the setting will
          persist until "-cleared" is given
        - "+future" will show all future entries; "-future" reverts to
          only showing future up to 4 days
        """
        args = util.parse_args(args)
        self.list_transactions()

    def do_account(self, args):
        """Print the account being reconciled"""
        print(self.ledgerfile.rec_account_matches_all[0])

    def list_transactions(self):

        count = 0
        for thing in self.ledgerfile.get_things():
            if not thing.rec_account_matches \
                    or thing.thing_date > date.today() + relativedelta(days=4) \
                    or thing.rec_status == '*':

                continue
            count += 1
            print(
                '{number:-4}. {date} {code:>7} {payee} '
                '{amount} {status:1}  |{number:-4} '
                '{thing_num:-6}'.format(
                    number=count,
                    date=thing.get_date_string(),
                    code=thing.transaction_code,
                    payee=get_colored_payee(thing.payee),
                    amount=get_colored_amount(thing.rec_amount),
                    status=thing.rec_status,
                    thing_num=thing.thing_number
                )
            )


def get_colored_amount(amount):
    if amount < 0:
        color = '\033[0;31m'  # red
    else:
        color = '\033[0;32m'  # green

    return '{start}${amount:10.2f}{end}'.format(
        start=color,
        amount=amount,
        end='\033[0m'
    )


def get_colored_payee(text):
    # cyan
    return '{start}{payee:40}{end}'.format(
        start='\033[0;36m',
        payee=text,
        end='\033[0m'
    )
