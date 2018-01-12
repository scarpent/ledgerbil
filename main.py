#!/usr/bin/env python3
import sys

from ledgerbil import ledgerbil
from ledgerbil.ledgershell import investments, prices


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        ledgerbil.main(argv)
        return

    if argv[0] == 'inv' or argv[0] == 'investments':
        investments.main(argv[1:])
        return

    if argv[0] == 'prices':
        prices.main(argv[1:])
        return

    ledgerbil.main(argv)


if __name__ == '__main__':
    sys.exit(main())  # pragma: no cover
