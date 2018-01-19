import argparse
import json

from .settings import Settings

settings = Settings()


def get_portfolio_report(args):
    return 'hi!'


def get_portfolio_data():
    with open(settings.PORTFOLIO_FILE, 'r') as portfile:
        return json.loads(portfile.read())


def get_args(args=[]):
    parser = argparse.ArgumentParser(
        prog='ledgerbil/main.py portfolio',
        formatter_class=(
            lambda prog: argparse.HelpFormatter(prog, max_help_position=36)
        )
    )
    parser.add_argument(
        '-a', '--accounts',
        type=str,
        default='.*',
        help='report on accounts that match this regex, default = .*'
    )

    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    print(get_portfolio_report(args))
