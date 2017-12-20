#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import subprocess
import sys

from settings import LEDGER_COMMAND, LEDGER_FILES, LEDGERDIR


def get_ledger_command(command_options=''):
    cmd = LEDGER_COMMAND
    for f in LEDGER_FILES:
        cmd += ' -f {}'.format(os.path.join(LEDGERDIR, f))
    cmd += ' {} '.format(command_options)
    return cmd


def get_ledger_output(command_options=''):
    cmd = get_ledger_command(command_options)
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print(error)
        sys.exit(1)
    return str(output)
