import re
from collections import namedtuple

DOLLARS_REGEX = re.compile(r'^\s*(?:(\$ -?[\d,.]+|0(?=  )))(.*)$')
SHARES_REGEX = re.compile(r'\s*(-?[\d,.]+) ([a-zA-Z]+)(.*)$')

Dollars = namedtuple('Dollars', 'amount account')
Shares = namedtuple('Shares', 'num symbol account')


# todo: parse out dollars and return float amount
def get_balance_line_dollars(line):
    match = re.match(DOLLARS_REGEX, line)
    if match:
        return Dollars(*match.groups())
    return None


def get_balance_line_shares(line):
    match = re.match(SHARES_REGEX, line)
    if match:
        return Shares(*match.groups())
    return None
