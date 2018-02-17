import argparse


def get_args(args=[]):
    parser = argparse.ArgumentParser(
        prog='ledgerbil/main.py grid',
        formatter_class=(lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=40,
            width=100
        ))
    )
    parser.add_argument(
        '-a', '--accounts',
        type=str,
        help='grid for specified accounts'
    )

    return parser.parse_args(args)


def main(argv=[]):
    args = get_args(argv)
    print(f'grid args: {args}')
