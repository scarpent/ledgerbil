#!/usr/bin/python

"""scheduler"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
from ledgerfile import LedgerFile
from schedulething import ScheduleThing


class Scheduler(object):

    def __init__(self, ledgerfile, schedulefile):
        self.ledgerfile = ledgerfile
        self.schedulefile = schedulefile

    def run(self):

        for schedulething in self.schedulefile.things:

            if schedulething.firstThing:
                sys.stderr.write('(first thing = file config thing)\n')
                continue

            if not schedulething.isScheduleThing:
                sys.stderr.write('ERROR: not a scheduleThing!\n')
                # todo: handle with error
                continue

            # print('a scheduleThing! date = %s' % schedulething.thingDate)
            # print('\tdays = %s, interval = %s, uom = %s'
            #       % (schedulething.days,
            #          schedulething.interval,
            #          schedulething.intervalUom))
            #
            # print('adding it to ledger file')

            self.ledgerfile.addThings(schedulething.getScheduledEntries())


