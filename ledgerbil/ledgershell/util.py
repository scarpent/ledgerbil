import re
from collections import namedtuple

from ..util import get_float

AMOUNT = r'-?[\d,.]+'
DOLLARS_REGEX = re.compile(rf"^\s*(?:(\$\s*{AMOUNT}|0(?=  )))(.*)$")
SHARES_REGEX = re.compile(rf"\s*({AMOUNT}) ([a-zA-Z]+)(.*)$")
FIRST_DOLLAR_AMOUNT_REGEX = re.compile(rf"^.*?\$\s*({AMOUNT}).*$")

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


def get_first_dollar_amount_float(line):
    DOLLARS = 0
    match = re.match(FIRST_DOLLAR_AMOUNT_REGEX, line)
    if match:
        return get_float(match.groups()[DOLLARS])
    return None
