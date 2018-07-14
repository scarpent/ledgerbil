import re
from collections import namedtuple

from ..util import get_float

DOLLARS_REGEX = re.compile(r'^\s*(?:(\$ -?[\d,.]+|0(?=  )))(.*)$')
SHARES_REGEX = re.compile(r'\s*(-?[\d,.]+) ([a-zA-Z]+)(.*)$')

AccountBalance = namedtuple('AccountBalance', 'account amount symbol')


def get_account_balance_new(line, shares=False, strip_account=True):
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
