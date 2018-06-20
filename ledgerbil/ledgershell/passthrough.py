import argparse
from textwrap import dedent

from .runner import get_ledger_command, get_ledger_output


def get_args(args):
    program = 'ledgerbil/main.py pass'
    description = dedent('''\
        Pass through args to ledger, running ledger with config from
        settings.py
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
        '--command',
        action='store_true',
        help='print ledger command used'
    )
    return parser.parse_known_args(args)


def main(argv=None):
    args, ledger_args = get_args(argv or [])
    if not ledger_args:
        return 0

    if args.command:
        print(' '.join(get_ledger_command(ledger_args)))

    print(get_ledger_output(ledger_args), end='')
