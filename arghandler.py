#!/usr/bin/python

"""do all the argparse stuff"""

from __future__ import print_function

import argparse


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class ArgHandler(object):

    @staticmethod
    def get_args(args):
        parser = argparse.ArgumentParser(
            prog='ledgerbil.py',
            formatter_class=(
                lambda prog: argparse.HelpFormatter(
                    prog,
                    max_help_position=36
                )
            )
        )

        parser.add_argument(
            '-f', '--file',
            type=str, required=True,
            help='ledger file to be processed'
        )
        parser.add_argument(
            '-s', '--sort',
            action='store_true',
            help='sort the file by transaction date'
        )
        parser.add_argument(
            '-r', '--reconcile',
            type=str, metavar='ACCT',
            help='reconcile the specified account'
        )
        parser.add_argument(
            '-S', '--schedule-file',
            type=str, metavar='FILE',
            help=(
                'file with scheduled transactions '
                '(to be added to -f ledger file)'
            )
        )

        return parser.parse_args(args)
