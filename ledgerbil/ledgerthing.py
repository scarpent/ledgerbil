"""objects in ledger file: transactions, etc"""

import re

from . import util
from .ledgerbilexceptions import LdgReconcilerError

UNSPECIFIED_PAYEE = '<Unspecified payee>'


class LedgerThing:

    DATE_REGEX = r'^\d{4}(?:[-/]\d\d){2}(?=(?:\s|$))'
    # todo: this could use improvement; if payee is omitted,
    #       there can't be a comment; also, must be at least
    #       two spaces between payee and comment
    #       (perhaps should just rely on ledger validation for one or both)
    TOP_LINE_REGEX = re.compile(
        r'(' + DATE_REGEX + ')'        # date
        r'(?:\s+\(([^)]*)\))?'         # optional transaction #
        r'\s*([^;]+)?'                 # optional payee
        r'(?:;.*$|$)'                  # optional comment
    )
    ENTRY_REGEX = re.compile(r'''(?x)  # verbose mode
        ^\s+                           # opening indent
        ([!*])?                        # optional pending/cleared
        (?:\s*)?                       # optional whitespace after p/c
        ([^;]+?)(?=\ \ |$)             # account (2 spaces ends acct)
        (?:\s*                         # optional share info, leading white
          (-?\s*[.,0-9]+)              # num shares
          (?:\s+([^@; ]+))             # symbol
          (?:\s*@\s*)?                 # optional @
        )?                             # close of optional share stuff
        \(?([-+*/()$\d.,\s]+)?\)?      # optional amount expression
        (?:;.*$|$)                     # optional end comment
        ''')
    REC_PENDING = '!'
    REC_CLEARED = '*'
    REC_UNCLEARED = ''

    def __init__(self, lines, reconcile_account=None):

        self.thing_number = 0
        self.thing_date = None
        self.payee = None
        self.transaction_code = ''  # e.g. check number
        self.lines = lines[:]
        self.is_transaction = False

        # reconciliation
        self.rec_account = reconcile_account  # could be partial
        self.rec_account_matched = None  # full account name
        self.rec_status = None
        self.rec_amount = 0  # can be dollars or num shares if rec_is_shares
        self.rec_is_shares = False
        self.rec_symbol = None

        if self.is_transaction_start(lines[0]):
            self.is_transaction = True
            self._parse_top_line(lines[0])

        if self.is_transaction and self.rec_account:
            self._parse_transaction_lines(lines[1:])

    def __repr__(self):
        return (f'{self.__class__.__name__}({self.get_lines()!r}, '
                f'reconcile_account={self.rec_account!r})')

    def __str__(self):
        return '\n'.join(self.get_lines())

    def _parse_top_line(self, line):
        m = re.match(LedgerThing.TOP_LINE_REGEX, line)

        the_date, code, payee = m.groups()

        # date can be modified
        self.thing_date = util.get_date(the_date)

        # payee and transaction code are read-only
        if code is not None:
            self.transaction_code = str(code)
        if payee is None or payee.strip() == '':
            self.payee = UNSPECIFIED_PAYEE
        else:
            self.payee = payee.strip()

    def _parse_transaction_lines(self, lines):
        if not self.rec_account or not lines:
            # We only care about transaction lines if reconciling
            return

        # There may be one or more lines for the account we're
        # reconciling. We only care about total for the account,
        # but we need to total everything up in case our account
        # doesn't have a dollar amount and we need to calculate it.
        transaction_total = 0
        account_total = 0
        need_math = False

        # There are lots of scenarios that are valid for ledger but
        # we're not handling for reconciliation. These sets are for
        # checking that things are as we desire.
        statuses = set()
        matched_accounts = set()
        shareses = set()
        symbols = set()

        for line in lines:
            m = re.match(self.ENTRY_REGEX, line)
            if not m:
                continue

            status, account, shares, symbol, amount = m.groups()

            if amount is not None:
                amount = amount.strip()
                if amount == '':
                    amount = None
                else:
                    amount = util.eval_expr(re.sub(r'[$,]', '', amount))
                    if shares is not None:
                        amount *= util.eval_expr(shares.replace(',', ''))
                    transaction_total += amount

            m = re.search(self.rec_account, account)
            if not m:
                continue

            matched_accounts.add(account)
            self.assert_only_one_matching_account(matched_accounts)

            statuses.add(status)
            self.assert_only_one_status(statuses)

            shareses.add(shares)
            if shares is not None:
                self.rec_is_shares = True
                symbols.add(symbol)
                self.assert_only_one_symbol(symbols)
                amount = float(re.sub(r'[, ]', '', shares))

            self.assert_only_shares_if_shares(shareses)

            if amount is None:
                # We're relying on a valid ledger file so that only one
                # entry can need math in a transaction
                need_math = True
            else:
                account_total += amount

        if need_math:
            # transaction_total should be 0; if math is needed, use
            # the part away from zero to figure out account_total
            account_total -= transaction_total

        self.rec_amount = account_total
        if matched_accounts:
            self.rec_account_matched = matched_accounts.pop()
            self.rec_status = statuses.pop()
            if symbols:
                self.rec_symbol = symbols.pop()

    def get_lines(self):
        if not self.is_transaction:
            return self.lines[:]

        lines_out = [re.sub(
            self.DATE_REGEX,
            self.get_date_string(),
            self.lines[0]
        )]

        if self.rec_account_matched is None:
            return lines_out + self.lines[1:]

        current_status = self.rec_status or ' '

        for line in self.lines[1:]:
            m = re.match(self.ENTRY_REGEX, line)
            if not m:  # e.g. a comment
                lines_out.append(line)
                continue

            status, account, shares, symbol, amount = m.groups()
            if re.search(self.rec_account, account):
                m = re.match(r'^\s+[!*]?\s*(.*)$', line)
                assert m
                # going to use a standard 4 space indent; alternatively
                # could try to be smart about preserving what is there
                lines_out.append('  {status} {remainder}'.format(
                    status=current_status,
                    remainder=m.groups()[0]
                ))
            else:
                lines_out.append(line)

        return lines_out[:]

    @staticmethod
    def is_new_thing(line):
        # currently, is_new_thing == is_transaction_start, but this
        # could change in future
        if LedgerThing.is_transaction_start(line):
            return True
        else:
            return False

    @staticmethod
    def is_transaction_start(line):
        match = re.match(LedgerThing.TOP_LINE_REGEX, line)
        if match:
            return util.is_valid_date(match.groups()[0])
        else:
            return False

    @staticmethod
    def assert_only_one_matching_account(accounts):
        if len(set(accounts)) > 1:
            message = 'More than one matching account:\n'
            for account in sorted(list(accounts)):
                message += f'    {account}\n'
            raise LdgReconcilerError(message[:-1])

    def assert_only_one_status(self, statuses):
        if len(set(statuses)) > 1:
            raise LdgReconcilerError(
                f'Unhandled multiple statuses: {self.get_date_and_payee()}'
            )

    def assert_only_one_symbol(self, symbols):
        if len(set(symbols)) > 1:
            raise LdgReconcilerError(
                'Unhandled multiple symbols: {}\n{}'.format(
                    sorted(list(set(symbols))),
                    '\n'.join(self.lines)
                )
            )

    def assert_only_shares_if_shares(self, shareses):
        if self.rec_is_shares and None in shareses:
            raise LdgReconcilerError(
                'Unhandled shares with non-shares:\n{}'.format(
                    '\n'.join(self.lines)
                )
            )

    def get_date_and_payee(self):
        return f'{self.get_date_string()} {self.payee}'

    def get_date_string(self):
        return util.get_date_string(self.thing_date)

    def is_pending(self):
        return self.rec_status == self.REC_PENDING

    def set_pending(self):
        self.rec_status = self.REC_PENDING

    def is_cleared(self):
        return self.rec_status == self.REC_CLEARED

    def set_cleared(self):
        self.rec_status = self.REC_CLEARED

    def set_uncleared(self):
        self.rec_status = self.REC_UNCLEARED
