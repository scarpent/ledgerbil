import ast
import operator as op
import re
import shlex
from datetime import datetime

from .colorable import Colorable

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
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., ~1
        return operators[type(node.op)](_eval(node.operand))
    else:
        raise TypeError(node)


def get_date_string(the_date):
    return the_date.strftime(DATE_FORMAT)


def get_date(date_string):
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
        print(f'*** {e}')
        return None


def get_decimals(is_shares):
    return 6 if is_shares else 2


def get_amount_str(amount, decimals=2):
    # avoid inconsistent zero signage from floating point machinations
    # (especially important for establishing if we're at zero for a
    # balanced statement)
    zero_amount = '{:.{}f}'.format(0, decimals)
    return re.sub(r'^-0.0+$', zero_amount, f'{amount:,.{decimals}f}')


def get_colored_amount(amount, column_width=1, is_shares=False):
    decimals = get_decimals(is_shares)
    dollar_sign = '' if is_shares else '$ '
    amount_formatted = '{}{}'.format(
        dollar_sign,
        get_amount_str(amount, decimals)
    )
    # avoid inconsistent 0 coloring from round/float intrigue
    if amount_formatted == f'{dollar_sign}{0:.{decimals}f}':
        amount = 0

    color = 'red' if amount < 0 else 'green'

    return str(Colorable(color, amount_formatted, f'>{column_width}'))
