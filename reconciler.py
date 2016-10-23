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

        count = 0
        for thing in self.ledgerfile.get_things():
            if not thing.rec_account_matches:
                continue
            count += 1
            print(
                '{number:-4}. {date} {code:>7} {payee:40} '
                '${amount:10.2f} {status}'.format(
                    number=count,
                    date=thing.get_date_string(),
                    code=thing.transaction_code,
                    payee=thing.payee,
                    amount=thing.rec_amount,
                    status=thing.rec_status
                )
            )
