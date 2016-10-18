#!/usr/bin/python

"""scheduler runner"""

from __future__ import print_function

from schedulething import ScheduleThing


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Scheduler(object):

    def __init__(self, ledgerfile, schedulefile):
        self.ledgerfile = ledgerfile
        self.schedulefile = schedulefile

    def run(self):

        if ScheduleThing.enter_days == ScheduleThing.NO_DAYS:
            return

        self.schedulefile.sort()

        for schedulething in self.schedulefile.things:

            if schedulething.first_thing:
                continue

            self.ledgerfile.add_things(
                schedulething.get_scheduled_entries()
            )

        self.schedulefile.sort()
