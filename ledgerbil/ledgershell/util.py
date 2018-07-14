import re
from collections import namedtuple

from ..util import get_float

DOLLARS_REGEX = re.compile(r'^\s*(?:(\$ -?[\d,.]+|0(?=  )))(.*)$')
SHARES_REGEX = re.compile(r'\s*(-?[\d,.]+) ([a-zA-Z]+)(.*)$')

Dollars = namedtuple('Dollars', 'amount account')
Shares = namedtuple('Shares', 'num symbol account')


def get_balance_line(line, shares=False, strip_account=True):
    if shares:
        get_balance = get_balance_line_shares
    else:
        get_balance = get_balance_line_dollars

    return get_balance(line, strip_account)


def get_balance_line_dollars(line, strip_account=True):
    match = re.match(DOLLARS_REGEX, line)
    if match:
        amount, account = match.groups()
        account = account.strip() if strip_account else account
        return Dollars(get_float(amount), account)
    return None


def get_balance_line_shares(line, strip_account=True):
    match = re.match(SHARES_REGEX, line)
    if match:
        num, symbol, account = match.groups()
        account = account.strip() if strip_account else account
        return Shares(num, symbol, account)
    return None
