#!/usr/bin/python

"""scheduler runner"""

from __future__ import print_function

from schedulething import ScheduleThing


__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Scheduler(object):

    def __init__(self, ledgerfile, schedulefile):
        self.ledgerfile = ledgerfile
        self.schedulefile = schedulefile

    def run(self):

        if ScheduleThing.enterDays == ScheduleThing.NO_DAYS:
            return

        self.schedulefile.sort()

        for schedulething in self.schedulefile.things:

            if schedulething.firstThing:
                continue

            self.ledgerfile.addThings(
                schedulething.getScheduledEntries()
            )

        self.schedulefile.sort()
