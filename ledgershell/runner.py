import os
import shlex
import subprocess
import sys

from .settings import Settings

s = Settings()


def get_ledger_command(options=''):
    cmd = s.LEDGER_COMMAND
    for f in s.LEDGER_FILES:
        cmd += ' -f {}'.format(os.path.join(s.LEDGER_DIR, f))
    cmd += ' {} '.format(options)
    return cmd


def get_ledger_output(options=''):
    cmd = get_ledger_command(options)
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print(error)
        sys.exit(1)
    return output.decode('unicode_escape')
