import cmd
import json
import os
import sys
from datetime import date

from . import util
from .colorable import Colorable
from .ledgerbilexceptions import LdgReconcilerError
from .settings import Settings

settings = Settings()


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
            'r': self.do_reload,
            's': self.do_show,
            'start': self.do_statement,
        }

        self.ledgerfile = ledgerfile
        self.ending_date = date.today()
        self.ending_balance = None
        self.previous_date = date.today()
        self.previous_balance = None
        self.cached_is_shares = None
        self.get_statement_info_from_cache()

        # these are immediately reset in populate open transactions
        self.open_transactions = []
        self.current_listing = {}
        self.total_cleared = 0
        self.total_pending = 0
        self.is_shares = False
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
                list(self.aliases.keys()),
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

        Syntax: list [all]

        - Shows uncleared and pending transactions (Pending = "!")
        - Pending transactions are always listed regardless of date
        - Uncleared transactions are listed up to the statement ending
          date (defaults to today)
        - "All" will list all uncleared transactions regardless of date
        """
        self.list_transactions(args)

    def do_account(self, args):
        """Print the account being reconciled"""
        print(self.ledgerfile.rec_account_matched)

    def do_mark(self, args):
        """Mark a transaction as pending (!)

        Syntax: mark <#> or <# ... #>
                <#>
                mark all

        - The numbered line of a transaction, or multiple numbers
          separated by spaces
        - Without "mark", a single transaction number
        - "all" to mark all uncleared transactions
        """
        self.mark_or_unmark(args, mark=True)

    def do_unmark(self, args):
        """Remove pending mark (!) from transaction

        Syntax: unmark <#>
                unmark all

        - The numbered line of a transaction, or multiple numbers
          separated by spaces
        - "all" to unmark all pending transactions
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

    def do_reload(self, args):
        """Reload the ledger file from storage"""
        self.reload()

    def do_show(self, args):
        """Show transaction details

        Syntax: show <#> or <# ... #>
        """
        self.show_transaction(args)

    def reload(self):
        self.ledgerfile.reset()
        self.populate_open_transactions()

    def show_transaction(self, args):
        args = util.parse_args(args)
        if not args:
            print('*** Transaction number(s) required')
            return

        messages = ''
        for num in args:
            if num not in self.current_listing:
                messages += f'Transaction not found: {num}\n'
                continue

            thing = self.current_listing[num]
            print()
            for line in thing.get_lines():
                print(line)

        if messages:
            print(messages, end='')

    def populate_open_transactions(self):
        self.open_transactions = []
        self.current_listing = {}
        self.total_cleared = 0
        self.total_pending = 0

        is_shareses = set()
        symbols = set()

        for thing in self.ledgerfile.get_things():
            if thing.rec_account_matched:
                is_shareses.add(thing.rec_is_shares)
                symbols.add(thing.rec_symbol)

                if thing.is_cleared():
                    self.total_cleared += thing.rec_amount
                    continue

                if thing.is_pending():
                    self.total_pending += thing.rec_amount

                self.open_transactions.append(thing)

        if self.open_transactions:
            self.validate_and_get_is_shares(is_shareses)
            self.assert_only_one_symbol(symbols)
        else:
            self.is_shares = self.cached_is_shares

        self.do_list('')

    def validate_and_get_is_shares(self, is_shareses):
        if len(is_shareses) == 1:
            self.is_shares = is_shareses.pop()
        else:
            raise LdgReconcilerError(
                'Unhandled shares with non-shares: "{}"'.format(
                    self.ledgerfile.rec_account_matched
                )
            )

    def assert_only_one_symbol(self, symbols):
        if self.is_shares and len(set(symbols)) != 1:
            raise LdgReconcilerError(
                'Unhandled multiple symbols: "{}": {}'.format(
                    self.ledgerfile.rec_account_matched,
                    sorted(list(symbols))
                )
            )

    def mark_or_unmark(self, args, mark=True):
        args = util.parse_args(args)
        if not args:
            print('*** Transaction number(s) required')
            return

        if args[0].lower() == 'all':
            args = []
            for key, thing in self.current_listing.items():
                if ((mark and not thing.is_pending())
                        or (not mark and thing.is_pending())):
                    args.append(key)

        at_least_one_success = False
        messages = ''
        for num in args:
            if num not in self.current_listing:
                messages += f'Transaction not found: {num}\n'
                continue

            thing = self.current_listing[num]

            if mark and thing.is_pending():
                messages += f'Already marked pending: {num}\n'
                continue
            elif not mark and not thing.is_pending():
                messages += f"Not marked; can't unmark: {num}\n"
                continue

            if mark:
                self.current_listing[num].set_pending()
                self.total_pending += thing.rec_amount
            else:
                thing.set_uncleared()
                self.total_pending -= thing.rec_amount

            at_least_one_success = True

        if at_least_one_success:
            self.ledgerfile.write_file()
            self.list_transactions()

        if messages:
            print(messages, end='')

    def list_transactions(self, args=None):
        args = util.parse_args(args)
        if args and args[0].lower() == 'all':
            show_all = True
        else:
            show_all = False

        self.current_listing = {}
        count = 0
        for thing in self.open_transactions:
            if thing.thing_date > self.ending_date \
                    and not show_all \
                    and not thing.is_pending():
                continue

            if not self.current_listing:
                print()  # only print one buffer line at top if items

            count += 1
            self.current_listing[str(count)] = thing
            count_str = f'{count:-4}.'
            print(
                '{number} {date} {amount} {status:1} {payee} {code:>7}'.format(
                    number=Colorable('cyan', count_str),
                    date=thing.get_date_string(),
                    code=thing.transaction_code,
                    payee=util.Colorable('cyan', thing.payee, 40),
                    amount=self.get_colored_amount(
                        thing.rec_amount,
                        colwidth=16 if self.is_shares else 11
                    ),
                    status=thing.rec_status or ''
                )
            )

        if self.previous_balance:
            print(
                '\nlast reconciled: {previous_date} '
                'previous balance: {previous_balance}'.format(
                    previous_date=Colorable(
                        'white',
                        util.get_date_string(self.previous_date)
                    ),
                    previous_balance=self.get_colored_amount(
                        self.previous_balance
                    )
                )
            )

        if self.ending_balance is None:
            end_balance = Colorable('cyan', '(not set)')
        else:
            end_balance = self.get_colored_amount(self.ending_balance)

        print(
            '{newline}ending date: {end_date} ending balance: {end_balance} '
            'cleared: {cleared}'.format(
                newline='' if self.previous_balance else '\n',
                cleared=self.get_colored_amount(self.total_cleared),
                end_balance=end_balance,
                end_date=Colorable(
                    'cyan',
                    util.get_date_string(self.ending_date)
                )
            )
        )

        if self.ending_balance is not None:
            print('to zero: {}'.format(
                self.get_colored_amount(self.get_zero_candidate())
            ))

        print()

    def cancel_statement(self, value):

        if value and value.lower() == 'cancel':
            previous_ending = self.ending_balance

            self.ending_date = date.today()
            self.ending_balance = None

            if previous_ending is not None:
                self.save_statement_info_to_cache()
                self.list_transactions()

            return True
        else:
            return False

    def set_statement_info(self):

        if self.ending_balance is not None:
            print(
                "(Enter 'cancel' to remove ending balance and set "
                "ending date to today.)"
            )

        old_ending_date = self.ending_date
        while True:
            date_str = util.get_date_string(self.ending_date)
            new_date = self.get_response(
                prompt='Ending Date (YYYY/MM/DD)',
                old_value=date_str
            )

            if self.cancel_statement(new_date):
                return

            try:
                self.ending_date = util.get_date(new_date)
                break
            except ValueError:
                print('*** Invalid date')

        new_ending_balance = None
        if self.ending_balance is None:
            old_ending_balance = None
        else:
            old_ending_balance = util.get_amount_str(
                self.ending_balance,
                decimals=self.get_decimals()
            )

        while True:
            new_ending_balance = self.get_response(
                prompt='Ending Balance',
                old_value=old_ending_balance
            )
            if new_ending_balance is None:
                break

            if self.cancel_statement(new_ending_balance):
                return

            try:
                self.ending_balance = float(
                    new_ending_balance.replace('$', '')
                )
                break
            except ValueError:
                print('*** Invalid number')

        if new_ending_balance is not None:
            new_ending_balance = util.get_amount_str(
                self.ending_balance,
                decimals=self.get_decimals()
            )

        # only list and save to cache if values have changed...
        if old_ending_date != self.ending_date \
                or old_ending_balance != new_ending_balance:
            self.save_statement_info_to_cache()
            self.list_transactions()

    def finish_balancing(self):

        if self.ending_balance is None:
            print('*** Ending balance must be set in order to finish')
            return

        if util.get_amount_str(self.get_zero_candidate()) != '0.00':
            print('"To zero" must be zero in order to finish')
            return

        for thing in self.open_transactions:
            if thing.is_pending():
                thing.set_cleared()

        self.previous_balance = self.ending_balance
        self.previous_date = date.today()
        self.ending_balance = None
        self.ending_date = date.today()
        self.cached_is_shares = self.is_shares
        self.save_statement_info_to_cache(finish=True)

        self.ledgerfile.write_file()
        self.populate_open_transactions()

    def get_zero_candidate(self):
        return (
            self.ending_balance - (self.total_cleared + self.total_pending)
        )

    @staticmethod
    def get_response(prompt='', old_value=''):
        default = old_value or ''
        response = input(f'{prompt} [{default}]: ').strip()

        if response == '':
            response = old_value

        return response

    def get_key_and_cache(self):
        key = self.ledgerfile.rec_account_matched

        if os.path.exists(settings.RECONCILER_CACHE_FILE):
            try:
                with open(settings.RECONCILER_CACHE_FILE, 'r') as the_file:
                    return key, json.loads(the_file.read())
            except (IOError, ValueError) as e:
                print(f'Error getting reconciler cache: {e}', file=sys.stderr)

        return key, {}

    def get_statement_info_from_cache(self):
        key, cache = self.get_key_and_cache()
        if key in cache:
            self.ending_date, self.ending_balance = \
                self.get_date_and_balance(key, cache, 'ending')

            self.previous_date, self.previous_balance = \
                self.get_date_and_balance(key, cache, 'previous')

            self.cached_is_shares = cache[key].get('shares', False)

    def get_date_and_balance(self, key, cache, prefix):
        the_date = util.get_date(cache[key].pop(
            f'{prefix}_date',
            util.get_date_string(date.today())
        ))
        the_balance = cache[key].pop(f'{prefix}_balance', None)
        return the_date, the_balance

    def save_statement_info_to_cache(self, finish=False):
        key, cache = self.get_key_and_cache()

        if self.ending_balance is None or finish:
            if key in cache:
                cache[key].pop('ending_date', None)
                cache[key].pop('ending_balance', None)
            if finish:
                entry = {
                    'previous_date': util.get_date_string(self.previous_date),
                    'previous_balance': self.previous_balance,
                    'shares': self.is_shares
                }
                cache[key] = entry
        else:
            cache[key] = cache.get(key, {})
            cache[key]['ending_date'] = util.get_date_string(self.ending_date)
            cache[key]['ending_balance'] = self.ending_balance

        try:
            with open(settings.RECONCILER_CACHE_FILE, 'w') as the_file:
                the_file.write(json.dumps(cache, indent=4, sort_keys=True))
        except (IOError, ValueError) as e:
            print(f'Error writing reconciler cache: {e}', file=sys.stderr)

    def get_decimals(self):
        return 6 if self.is_shares else 2

    def get_colored_amount(self, amount, colwidth=1):
        prefix = '' if self.is_shares else '$ '
        decimals = self.get_decimals()
        return util.get_colored_amount(amount, colwidth, decimals, prefix)
