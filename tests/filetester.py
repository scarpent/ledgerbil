#!/usr/bin/python

"""unit test for ledgerfile.py"""

import inspect  # inspect.stack()[1][3] gives name of calling function

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

    mainfile = 'ledgerbil.py'

    @staticmethod
    def create_temp_file(testdata):
        tempfile = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        return tempfile

    @staticmethod
    def copy_to_temp_file(filename):
        tempfile = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        copyfile(filename, tempfile)
        return tempfile

    @staticmethod
    def read_file(filename):
        f = open(filename, 'r')
        testdata = f.read()
        f.close()
        return testdata

    @staticmethod
    def write_to_temp_file(filename, testdata):
        tempfile = filename + '_temp'
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        return tempfile
