#!/usr/bin/python

"""do all the argparse stuff"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import argparse


class ArgHandler():

    @staticmethod
    def getArgs():
        parser = argparse.ArgumentParser()

        parser.add_argument(
            '-f', '--file',
            type=str, required=True, help='ledger file to be processed'
        )
        parser.add_argument(
            '-s', '--sort',
            help='sort the file by transaction date', action='store_true'
        )
        parser.add_argument(
            '-S', '--schedule-file',
            type=str, metavar='FILE',
            help='file with scheduled transactions (to be added to -f ledger file)'
        )
        parser.add_argument(
            '-p', '--preview-file',
            type=str, metavar='FILE',
            help='file for previewed scheduled transactions (will be overwritten)'
        )

        return parser.parse_args()
