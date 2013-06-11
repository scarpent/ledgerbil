#!/usr/bin/python

"""scheduler"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from ledgerfile import LedgerFile
from schedulething import ScheduleThing


class Scheduler(object):

    def __init__(self, ledgerfile, schedulefile):
        self.ledgerfile = ledgerfile
        self.schedulefile = schedulefile

    def run(self):

        for schedulething in self.schedulefile.things:

            if not schedulething.isScheduleThing:
                print('not a scheduleThing...')  # todo: temp for dev/debug
                continue

            print('a scheduleThing! date = %s' % schedulething.date)
            print('\tdays = %s, interval = %s, uom = %s'
                  % (schedulething.days,
                     schedulething.interval,
                     schedulething.intervalUom))

            print('adding it to ledger file')

            self.ledgerfile.addThings(schedulething.getScheduledEntries())


