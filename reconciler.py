#!/usr/bin/python

from __future__ import print_function


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Reconciler(object):

    def __init__(self, ledgerfile):
        self.ledgerfile = ledgerfile

    def run(self):

        self.schedulefile.sort()

        for schedulething in self.schedulefile.things:

            if schedulething.first_thing:
                continue

            self.ledgerfile.add_things(
                schedulething.get_scheduled_entries()
            )

        self.schedulefile.sort()
