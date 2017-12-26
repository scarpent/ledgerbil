#!/usr/bin/env python3

import sys

from ledgerbil import ledgerbil
from ledgershell import investments, prices

argv = sys.argv[1:]

if argv:
    if argv[0] == 'inv' or argv[0] == 'investments':
        investments.main(argv[1:])
        sys.exit(0)
    if argv[0] == 'prices':
        prices.main(argv[1:])
        sys.exit(0)

ledgerbil.main(argv)
