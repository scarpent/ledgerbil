import os
import shlex
import subprocess
import sys

from ..settings import Settings

settings = Settings()


def get_ledger_command(options=''):
    cmd = settings.LEDGER_COMMAND
    for f in settings.LEDGER_FILES:
        cmd += f' -f {os.path.join(settings.LEDGER_DIR, f)}'
    cmd += f' {options} '
    return cmd


def get_ledger_output(options=''):
    cmd = get_ledger_command(options)
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print(error)
        sys.exit(1)
    return output.decode('unicode_escape')
