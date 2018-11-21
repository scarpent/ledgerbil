from .ledgerbilexceptions import LdgSchedulerError
from .schedulefile import ScheduleFile
from .schedulething import ScheduleThing
from .util import handle_error


def run_scheduler(ledgerfile, schedule_filename):
    schedulefile = None
    try:
        schedulefile = ScheduleFile(schedule_filename)
    except LdgSchedulerError as e:
        return handle_error(str(e))

    print(f'Schedule file (enter days = {ScheduleThing.enter_days}):')

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

    entries = 'entry' if things_added == 1 else 'entries'
    print(f'Added {things_added} {entries}')

    schedulefile.sort()
    schedulefile.write_file()
    ledgerfile.write_file()


def print_next_scheduled_date(schedule_filename):
    try:
        schedule_file = ScheduleFile(schedule_filename)
    except LdgSchedulerError as e:
        return handle_error(str(e))

    print(schedule_file.next_scheduled_date())
