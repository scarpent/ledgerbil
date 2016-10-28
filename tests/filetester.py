#!/usr/bin/env python

"""unit test for ledgerfile.py"""

import inspect  # inspect.stack()[1][3] gives name of calling function
import os
import tempfile

from contextlib import contextmanager
from shutil import copyfile


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class FileTester(object):

    testdir = 'tests/files/'

    testfile = testdir + 'test.ledger'
    sortedfile = testdir + 'test-already-sorted.ledger'
    alpha_unsortedfile = testdir + 'test-alpha-unsorted.ledger'
    alpha_sortedfile = testdir + 'test-alpha-sorted.ledger'
    readonlyfile = testdir + 'test-read-only.ledger'

    testschedulefileledger = testdir + 'test-schedule.ledger'
    test_enter_lessthan1 = testdir + 'test-schedule-enter-days-lt1.ldg'

    test_rec_multiple_match = testdir + 'reconcile-multiple-match.ldg'
    test_reconcile = testdir + 'reconcile.ledger'

    @staticmethod
    def create_temp_file(testdata):
        temp_file = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        f = open(temp_file, 'w')
        f.write(testdata)
        f.close()
        return temp_file

    @staticmethod
    def copy_to_temp_file(filename):
        temp_file = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        copyfile(filename, temp_file)
        return temp_file

    @staticmethod
    def read_file(filename):
        f = open(filename, 'r')
        testdata = f.read()
        f.close()
        return testdata

    @staticmethod
    def write_to_temp_file(filename, testdata):
        temp_file = filename + '_temp'
        f = open(temp_file, 'w')
        f.write(testdata)
        f.close()
        return temp_file

    @staticmethod
    @contextmanager
    def temp_input(data):
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(data)
        temp.close()
        yield temp.name
        os.unlink(temp.name)
