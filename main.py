#!/usr/bin/env python3
import sys

from ledgerbil import ledgerbil, portfolio
from ledgerbil.ledgershell import grid, investments, passthrough, prices


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    command = argv[0] if argv else ''

    other = {
        'grid': grid,
        'inv': investments,
        'investments': investments,
        'pass': passthrough,
        'port': portfolio,
        'portfolio': portfolio,
        'prices': prices,
    }

    if command not in other:
        ledgerbil.main(argv)
    else:
        other[command].main(argv[1:])


if __name__ == '__main__':
    sys.exit(main())  # pragma: no cover
