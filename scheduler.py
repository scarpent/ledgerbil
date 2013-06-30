#!/usr/bin/python

"""scheduler"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys

class Scheduler(object):

    def __init__(self, ledgerfile, schedulefile):
        self.ledgerfile = ledgerfile
        self.schedulefile = schedulefile

    def run(self):

        for schedulething in self.schedulefile.things:

            if schedulething.firstThing:
                continue

            if not schedulething.isScheduleThing:
                sys.stderr.write('ERROR: not a scheduleThing!\n')
                # todo: handle with error
                continue

            self.ledgerfile.addThings(schedulething.getScheduledEntries())


