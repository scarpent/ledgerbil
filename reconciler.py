#!/usr/bin/python

from __future__ import print_function


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Reconciler(object):

    def __init__(self, ledgerfile, account):
        self.ledgerfile = ledgerfile
        self.account = account

    def run(self):
        print('todo: reconcile ' + self.account)
