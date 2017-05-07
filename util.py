#!/usr/bin/env python

import ast
import operator as op
import re
import shlex
from datetime import datetime

__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


DATE_FORMAT = '%Y/%m/%d'

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg, ast.Invert: op.invert}


# eval_expr / _eval from: http://stackoverflow.com/a/9558001/2374860
def eval_expr(expr):
    return _eval(ast.parse(expr, mode='eval').body)


def _eval(node):
    if isinstance(node, ast.Num):  # <number> e.g. 1 or -1
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](
            _eval(node.left), _eval(node.right)
        )
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., ~1
        return operators[type(node.op)](_eval(node.operand))
    else:
        raise TypeError(node)


def get_date_string(the_date):
    """ @type the_date: date """
    return the_date.strftime(DATE_FORMAT)


def get_date(date_string):
    """ @type date_string: str """
    return datetime.strptime(date_string, DATE_FORMAT).date()


def is_valid_date(date_string):
    try:
        get_date(date_string)
        return True
    except ValueError:
        return False


def is_integer(value):
    try:
        if value[0] in ('-', '+'):
            return value[1:].isdigit()
        return value.isdigit()
    except (TypeError, IndexError):
        return False


def parse_args(args):
    # args should be a string, but we'll make sure it isn't None
    # (which would cause the string to be read from stdin)
    try:
        return shlex.split(args if args else '')
    except ValueError as e:
        print('*** '.format(e))
        return None


def get_amount_str(amount):
    # avoid inconsistent zero signage from floating point machinations
    # (especially important for establishing if we're at zero for a
    # balanced statement)
    return re.sub(r'^-0.00$', '0.00', '{:.2f}'.format(amount))


def get_colored_amount(amount, column_width=1):
    amount_formatted = '$' + get_amount_str(amount)
    # avoid inconsistent 0 coloring from round/float intrigue
    if amount_formatted == '$0.00':
        amount = 0

    if amount < 0:
        color = '\033[0;31m'  # red
    else:
        color = '\033[0;32m'  # green

    return '{start}{amount:>{width}}{end}'.format(
        width=column_width,
        start=color,
        amount=amount_formatted,
        end='\033[0m'
    )


def get_cyan_text(text, column_width=1):
    return '{start}{text:{width}}{end}'.format(
        width=column_width,
        start='\033[0;36m',
        text=text,
        end='\033[0m'
    )
