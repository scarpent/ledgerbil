import argparse
import re
import shlex
from textwrap import dedent

from ..colorable import Colorable
from ..settings import Settings
from .runner import get_ledger_command, get_ledger_output
from .util import AccountBalance, get_account_balance

settings = Settings()


def get_investment_command_options(
        shares=False,
        accounts=settings.INVESTMENT_DEFAULT_ACCOUNTS,
        end_date=settings.INVESTMENT_DEFAULT_END_DATE):

    options = []
    if shares:
        options += ['--exchange', '.']  # override --market
    options += ['--end', end_date]

    return tuple(['bal'] + shlex.split(accounts) + options)


def warn_negative_dollars(amount, account):
    print(
        '{warning} Negative dollar amount {amount} for "{account}". '
        'This may be a data entry mistake, or because we are '
        'looking at a date range.\n'.format(
            warning=Colorable('red', 'WARNING:'),
            amount=Colorable('red', amount),
            account=account.strip()
        )
    )


def get_lines(args, shares=False):
    options = get_investment_command_options(shares, args.accounts, args.end)
    output = get_ledger_output(options)

    if args.command:
        print(' '.join(get_ledger_command(options)))

    return output.split('\n')


def get_dollars(args):
    """ A sample dollars report:

                  $ 1,737.19  assets
                  $ 1,387.19     401k
                    $ 798.19       big co 500 idx
                    $ 400.00       bonds idx
                    $ 189.00       cash
                    $ 150.00     ira: glass idx
                    $ 200.00     mutual: total idx
        --------------------
                  $ 1,737.19
    """
    listing = []
    lines = get_lines(args)
    for line in lines:
        if line == '' or line[0] == '-':
            break
        dollars = get_account_balance(line, strip_account=False)
        assert dollars, f'Did not find expected account and dollars: {line}'
        if dollars.amount < 0:
                warn_negative_dollars(dollars.amount, dollars.account)
        listing.append(dollars)

    return listing


def get_shares(args):
    """ A sample share report to help make sense of this. We will turn this
        odd lump of output into a list that matches the much nicer dollars
        report shown above.

                    $ 189.00
                 9.897 abcdx
                20.000 lmnop
                15.000 qwrty
                 5.000 yyzxx  assets
                    $ 189.00
                 9.897 abcdx
                20.000 lmnop     401k
                 9.897 abcdx       big co 500 idx
                20.000 lmnop       bonds idx
                    $ 189.00       cash
                15.000 qwrty     ira: glass idx
                 5.000 yyzxx     mutual: total idx
        --------------------
                    $ 189.00
                 9.897 abcdx
                20.000 lmnop
                15.000 qwrty
                 5.000 yyzxx
    """
    listing = []
    lines = get_lines(args, shares=True)
    # Filter out all the lines not attached to an account name; after
    # this our share list will be the same length as our dollars list,
    # with one line per account "level"
    # (Note: We can't handle multiple symbols for an account. Should
    #        we catch this and error out?)
    lines = [x for x in lines if re.search(r'\S  ', x)]
    # Reverse the list to make it easier to find leaf nodes in the
    # indented tree structure of account names
    last_indent = 0
    for line in reversed(lines):
        dollars = get_account_balance(line, strip_account=False)
        if dollars:
            # Cash lines don't have share amounts, just dollars; we'll
            # make share amount be 0 and symbol empty and just have the
            # account to keep our lists lined up
            if dollars.amount < 0:
                warn_negative_dollars(
                    dollars.amount,
                    dollars.account
                )
            shares = AccountBalance(dollars.account, 0, '')
        else:
            shares = get_account_balance(
                line,
                shares=True,
                strip_account=False
            )
            assert shares, f'Did not find expected account and shares: {line}'

        # Only use the shares from the leaf nodes, which will be
        # at the same indent or further indented
        indent = (
            len(shares.account) - len(shares.account.strip())
        )
        if indent < last_indent:
            # Same as with cash lines, make share amount 0 and symbol empty
            shares = AccountBalance(shares.account, 0, '')
        last_indent = indent

        listing.append(shares)

    listing.reverse()  # Reverse back to match dollars list order
    return listing


def get_investment_report(args):
    """ We want to put the separate shares and dollars reports
        together to get something like this:

                           $ 1,737.19   assets
                           $ 1,387.19      401k
         9.897 abcdx         $ 798.19        big co 500 idx
        20.000 lmnop         $ 400.00        bonds idx
                             $ 189.00        cash
        15.000 qwrty         $ 150.00      ira: glass idx
         5.000 yyzxx         $ 200.00      mutual: total idx
    """
    share_listing = get_shares(args)
    dollar_listing = get_dollars(args)

    report = ''

    for shares, dollars in zip(share_listing, dollar_listing):

        err_message = (f'Non-matching accounts. Shares: {shares.account}, '
                       f'Dollars: {dollars.account}')
        assert shares.account == dollars.account, err_message

        dollar_color = 'red' if dollars.amount < 0 else 'green'
        dollars_f = '0' if dollars.amount == 0 else f'$ {dollars.amount:,.2f}'
        shares_amount_f = '' if shares.amount == 0 else f'{shares.amount:,}'

        report += ('{shares} {symbol} {dollars} {investment}\n'.format(
            shares=Colorable('gray', shares_amount_f, '>12', bright=True),
            symbol=Colorable('purple', shares.symbol, 5),
            dollars=Colorable(dollar_color, dollars_f, '>16'),
            investment=Colorable('blue', dollars.account)
        ))

    return report


def get_args(args):
    program = 'ledgerbil/main.py inv'
    description = dedent('''\
        Viewing shares with --exchange is kind of weird in ledger. This creates
        a report that shows share totals and dollar amounts in a nicer way.
    ''')
    parser = argparse.ArgumentParser(
        prog=program,
        description=description,
        formatter_class=(lambda prog: argparse.RawDescriptionHelpFormatter(
            prog,
            max_help_position=40,
            width=71
        ))
    )
    parser.add_argument(
        '-a', '--accounts',
        type=str,
        default=settings.INVESTMENT_DEFAULT_ACCOUNTS,
        help='balances for specified accounts (default: {})'.format(
            settings.INVESTMENT_DEFAULT_ACCOUNTS
        )
    )
    parser.add_argument(
        '-e', '--end',
        type=str,
        metavar='DATE',
        default=settings.INVESTMENT_DEFAULT_END_DATE,
        help=f'end date (default: {settings.INVESTMENT_DEFAULT_END_DATE})'
    )
    parser.add_argument(
        '-c', '--command',
        action='store_true',
        help='print ledger commands used'
    )

    return parser.parse_args(args)


def main(argv=None):
    args = get_args(argv or [])
    print(get_investment_report(args))
