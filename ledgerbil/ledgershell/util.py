import re
from collections import namedtuple

from ..util import get_float

DOLLARS_REGEX = re.compile(r'^\s*(?:(\$\s*-?[\d,.]+|0(?=  )))(.*)$')
SHARES_REGEX = re.compile(r'\s*(-?[\d,.]+) ([a-zA-Z]+)(.*)$')

# example match: '17-Feb-09 - 17-May-30   <Total>   $ 90.00   $ 90.00'
PAYEE_SUBTOTAL_REGEX = re.compile(r'^.*?\$\s*(\S+)\s*\$.*$')

AccountBalance = namedtuple('AccountBalance', 'account amount symbol')


def get_account_balance(line, shares=False, strip_account=True):
    if shares:
        match = re.match(SHARES_REGEX, line)
        if match:
            amount, symbol, account = match.groups()
    else:
        match = re.match(DOLLARS_REGEX, line)
        if match:
            amount, account = match.groups()
            symbol = '$'

    if not match:
        return None

    return AccountBalance(
        account.strip() if strip_account else account,
        get_float(amount),
        symbol
    )


def get_account_balance_generic(line):
    balance = get_account_balance(line, shares=False)
    if not balance:
        return get_account_balance(line, shares=True)
    return balance


def get_payee_subtotal(line):
    DOLLARS = 0
    match = re.match(PAYEE_SUBTOTAL_REGEX, line)
    if match:
        return get_float(match.groups()[DOLLARS])
    return None
