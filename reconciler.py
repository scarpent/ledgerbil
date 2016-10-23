#!/usr/bin/python

from __future__ import division
from __future__ import print_function


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class Reconciler(object):

    def __init__(self, ledgerfile, account):
        self.ledgerfile = ledgerfile
        self.account = account

    def run(self):

        for thing in self.ledgerfile.get_things():
            if not thing.is_transaction:
                continue

            print('{date} {code:>5} {payee}'.format(
                date=thing.get_date_string(),
                code=thing.transaction_code,
                payee=thing.payee
            ))
