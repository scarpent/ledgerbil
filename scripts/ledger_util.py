#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import subprocess
import sys

from settings import Settings

s = Settings()


def get_ledger_command(options=''):
    cmd = s.LEDGER_COMMAND
    for f in s.LEDGER_FILES:
        cmd += ' -f {}'.format(os.path.join(s.LEDGER_DIR, f))
    cmd += ' {} '.format(options)
    return cmd


def get_ledger_output(options=''):
    cmd = get_ledger_command(options)
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print(error)
        sys.exit(1)
    return str(output)
