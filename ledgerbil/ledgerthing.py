"""objects in ledger file: transactions, etc"""
import re
from collections import namedtuple

from . import util
from .ledgerbilexceptions import LdgReconcilerError

UNSPECIFIED_PAYEE = '<Unspecified payee>'

DATE_REGEX = r'^\d{4}(?:[-/]\d\d){2}(?=\s|$)'
# not matching optional comment since we don't do anything with it
TOP_LINE_REGEX = re.compile(
    r'(' + DATE_REGEX + r')(?:\s+|$)'  # date with required whitespace (or $)
    r'\s*([!*])?\s*'                   # optional transaction state (c/p)
    r'(?:\(([^)]*)\)\s*)?'             # optional transaction # and whitespace
    r'(.*?)(?=  |$)'                   # opt. payee ends with two spaces (or $)
)
# todo: should require amount when @ symbol is found
POSTING_REGEX = re.compile(r'''(?x)  # verbose mode
    ^\s+                             # opening indent
    ([!*])?                          # optional pending/cleared
    (?:\s*)?                         # optional whitespace after p/c
    ([^;]+?)(?<=\S)(?=\ \ |$)        # account - 2 spaces ends acct
    (?:\s*                           # optional share info, leading whitespace
      (-?\s*[.,0-9]+)                # num shares
      (?:\s*([^@; ]+))               # symbol
      (?:\s*@\s*)?                   # optional @
    )?                               # close of optional share stuff
    \(?([-+*/()$\d.,\s]+)?\)?        # optional amount expression
    (?:\s*=\s*[^;]+\s*)?             # optional balance assertion
    (?:;.*$|$)                       # optional end comment
    ''')
REC_PENDING = '!'
REC_CLEARED = '*'
REC_UNCLEARED = ''

LedgerPosting = namedtuple(
    'LedgerPosting',
    'status account shares symbol amount'
)


def get_ledger_posting(line):
    m = re.match(POSTING_REGEX, line)
    if not m:
        return None

    status, account, shares, symbol, amount = m.groups()

    if shares is not None:
        shares = util.get_float(shares)

    if amount is not None:
        amount = amount.strip()
        if amount == '':
            amount = None
        else:
            amount = util.eval_expr(re.sub(r'[$,]', '', amount))
            if shares is not None:
                amount *= shares

    return LedgerPosting(status, account, shares, symbol, amount)


class LedgerThing:

    def __init__(self, lines, reconcile_account=None):
        self.thing_number = None
        self.thing_date = None
        self.payee = None
        self.transaction_code = ''  # e.g. check number
        self.lines = list(lines)
        self.is_transaction = False

        # reconciliation
        self.rec_account = reconcile_account  # could be partial
        self.rec_account_matched = None  # full account name
        self.rec_status = None
        self.rec_amount = 0  # can be dollars or num shares if rec_is_shares
        self.rec_is_shares = False
        self.rec_symbol = None

        # not currently supported by reconciler - error out if matched account
        self.rec_top_line_status = False  # e.g. 2018/07/07 * payee name

        if self.is_transaction_start(lines[0]):
            self.is_transaction = True
            self.parse_top_line(lines[0])

        if self.is_transaction and self.rec_account:
            self.parse_transaction_lines(lines[1:])

    def __repr__(self):
        return (f'{self.__class__.__name__}({self.get_lines()}, '
                f'reconcile_account={self.rec_account})')

    def __str__(self):
        return '\n'.join(self.get_lines())

    def parse_top_line(self, line):
        m = re.match(TOP_LINE_REGEX, line)

        the_date, status, code, payee = m.groups()

        # date can be modified
        self.thing_date = util.get_date(the_date)

        if status:
            self.rec_top_line_status = True  # pending or cleared

        # payee and transaction code are read-only
        if code is not None:
            self.transaction_code = str(code)
        if payee is None or payee.strip() == '':
            self.payee = UNSPECIFIED_PAYEE
        else:
            self.payee = payee.strip()

    def parse_transaction_lines(self, lines):
        if not self.rec_account or not lines:
            # We only care about transaction lines if reconciling
            return

        # There may be one or more lines for the account we're
        # reconciling. We only care about total for the account,
        # but we need to total everything up in case our account
        # doesn't have a dollar amount and we need to calculate it.
        transaction_total = 0  # Always in dollars
        account_total = 0  # Dollars or number of shares
        need_math = False

        # There are lots of scenarios that are valid for ledger but
        # we're not handling for reconciliation. These sets are for
        # checking that things are as we desire.
        statuses = set()
        matched_accounts = set()
        shareses = set()
        symbols = set()

        for line in lines:
            posting = get_ledger_posting(line)
            if not posting:
                continue

            if posting.amount is not None:
                transaction_total += posting.amount

            m = re.search(self.rec_account, posting.account)
            if not m:
                continue

            self.assert_not_top_line_status()

            matched_accounts.add(posting.account)
            util.assert_only_one_matching_account(matched_accounts)

            statuses.add(posting.status)
            self.assert_only_one_status(statuses)

            shareses.add(posting.shares)
            if posting.shares is not None:
                self.rec_is_shares = True
                symbols.add(posting.symbol)
                self.assert_only_one_symbol(symbols)
                # We're interested in number of shares rather than $ amount
                account_amount = posting.shares
            else:
                account_amount = posting.amount

            self.assert_only_shares_if_shares(shareses)

            if account_amount is None:
                # We're relying on a valid ledger file so that only one
                # entry can need math in a transaction. With ledgerbil's
                # current understanding of things, math will only ever be
                # needed for dollar amounts, not share amounts.
                need_math = True
            else:
                account_total += account_amount

        if need_math:
            # Transaction_total should be 0; if math is needed, use
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
            return list(self.lines)

        lines_out = [re.sub(DATE_REGEX, self.get_date_string(), self.lines[0])]

        if self.rec_account_matched is None:
            return lines_out + self.lines[1:]

        current_status = self.rec_status or ' '

        for line in self.lines[1:]:
            posting = get_ledger_posting(line)
            if not posting:  # i.e. a comment
                lines_out.append(line)
                continue

            if re.search(self.rec_account, posting.account):
                m = re.match(r'^\s+[!*]?\s*(.*)$', line)
                assert m
                # going to use a standard 4 space indent; alternatively
                # could try to be smart about preserving what is there
                remainder = m.groups()[0]
                lines_out.append(f'  {current_status} {remainder}')
            else:
                lines_out.append(line)

        return list(lines_out)

    @staticmethod
    def is_new_thing(line):
        # currently, is_new_thing == is_transaction_start, but this
        # could change in future
        return LedgerThing.is_transaction_start(line)

    @staticmethod
    def is_transaction_start(line):
        match = re.match(TOP_LINE_REGEX, line)
        if match:
            return util.is_valid_date(match.groups()[0])
        else:
            return False

    def assert_only_one_status(self, statuses):
        if len(set(statuses)) > 1:
            raise LdgReconcilerError(
                f'Unhandled multiple statuses: {self.get_date_and_payee()}'
            )

    def assert_only_one_symbol(self, symbols):
        if len(set(symbols)) > 1:
            sorted_list = sorted(list(set(symbols)))
            formatted_lines = '\n'.join(self.lines)
            raise LdgReconcilerError(
                f'Unhandled multiple symbols: {sorted_list}\n{formatted_lines}'
            )

    def assert_only_shares_if_shares(self, shareses):
        """ ledgerbil isn't smart enough yet to handle a scenario like this:

        2018/07/08 zombie investments
            a: abc: xyz: little co idx                        2.345 abcdx
            a: 401k: big co 500 idx

        ledger can and will assume the elided amount is -2.345 abcdx, but
        ledgerbil assumes elided amounts are in dollars; ledger will
        further handle scenarios with multiple commodities that are *far*
        outside ledgerbil's reconciliation scope:

        https://www.ledger-cli.org/3.0/doc/ledger3.html#Eliding-amounts
        """
        if self.rec_is_shares and None in shareses:
            formatted_lines = '\n'.join(self.lines)
            raise LdgReconcilerError(
                f'Unhandled shares with non-shares:\n{formatted_lines}'
            )

    def assert_not_top_line_status(self):
        if self.rec_top_line_status:
            raise LdgReconcilerError(
                f'Unhandled top line transaction status:\n{self.lines[0]}'
            )

    def get_date_and_payee(self):
        return f'{self.get_date_string()} {self.payee}'

    def get_date_string(self):
        return util.get_date_string(self.thing_date)

    def is_pending(self):
        return self.rec_status == REC_PENDING

    def set_pending(self):
        self.rec_status = REC_PENDING

    def is_cleared(self):
        return self.rec_status == REC_CLEARED

    def set_cleared(self):
        self.rec_status = REC_CLEARED

    def set_uncleared(self):
        self.rec_status = REC_UNCLEARED
