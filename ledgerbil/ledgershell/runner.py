import os
import subprocess
import sys

from ..settings import Settings

settings = Settings()


def get_ledger_command(args=[]):
    files = []
    for f in settings.LEDGER_FILES:
        files += ['-f', os.path.join(settings.LEDGER_DIR, f)]
    return settings.LEDGER_COMMAND + files + args


def get_ledger_output(args=[]):
    cmd = get_ledger_command(args)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        print(error)
        sys.exit(1)
    return output.decode('unicode_escape')
