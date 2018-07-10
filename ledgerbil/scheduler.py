import sys

from .ledgerbilexceptions import LdgSchedulerError
from .schedulefile import ScheduleFile
from .schedulething import ScheduleThing


def run_scheduler(ledgerfile, schedule_filename):
    schedulefile = None
    try:
        schedulefile = ScheduleFile(schedule_filename)
    except LdgSchedulerError as e:
        return scheduler_error(str(e))

    print('Schedule file (enter days = {days}):'.format(
        days=ScheduleThing.enter_days
    ))

    if ScheduleThing.enter_days == 0:
        return

    schedulefile.sort()

    things_added = 0
    for schedulething in schedulefile.things:
        if schedulething.first_thing:
            continue

        things = schedulething.get_scheduled_entries()
        ledgerfile.add_things(things)
        things_added += len(things)

        for thing in things:
            print(f'\t{thing.thing_date} {thing.payee}')

    print('Added {num} {entries}'.format(
        num=things_added,
        entries='entry' if things_added == 1 else 'entries'
    ))

    schedulefile.sort()
    schedulefile.write_file()
    ledgerfile.write_file()


def scheduler_error(message):
    print(message, file=sys.stderr)
    return -1
