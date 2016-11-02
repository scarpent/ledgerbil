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

    CACHE_FILE_TEST = testdir + '.ledgerbil_cache_test'

    @staticmethod
    def create_temp_file(testdata):
        temp_file = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        with open(temp_file, 'w') as f:
            f.write(testdata)
        return temp_file

    @staticmethod
    def copy_to_temp_file(filename):
        temp_file = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        copyfile(filename, temp_file)
        return temp_file

    @staticmethod
    def read_file(filename):
        with open(filename, 'r') as f:
            return f.read()

    @staticmethod
    def write_to_temp_file(filename, testdata):
        temp_file = filename + '_temp'
        with open(temp_file, 'w') as f:
            f.write(testdata)
        return temp_file

    @staticmethod
    @contextmanager
    def temp_input(data):
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(data)
        yield temp.name
        os.unlink(temp.name)

    @staticmethod
    def delete_test_cache_file():
        if os.path.exists(FileTester.CACHE_FILE_TEST):
            os.remove(FileTester.CACHE_FILE_TEST)
