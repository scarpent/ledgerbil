from .schedulething import ScheduleThing


class Scheduler:

    def __init__(self, ledgerfile, schedulefile):
        self.ledgerfile = ledgerfile
        self.schedulefile = schedulefile

    def run(self):

        print('Schedule file (enter days = {days}):'.format(
            days=ScheduleThing.enter_days
        ))

        if ScheduleThing.enter_days == 0:
            return

        self.schedulefile.sort()

        things_added = 0
        for schedulething in self.schedulefile.things:

            if schedulething.first_thing:
                continue

            things = schedulething.get_scheduled_entries()
            self.ledgerfile.add_things(things)
            things_added += len(things)

            for thing in things:
                print(f'\t{thing.thing_date} {thing.payee}')

        print('Added {num} {entries}'.format(
            num=things_added,
            entries='entry' if things_added == 1 else 'entries'
        ))

        self.schedulefile.sort()
