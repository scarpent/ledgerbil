#!/usr/bin/python

"""unit test for ledgerfile.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import inspect  # inspect.stack()[1][3] gives name of calling function
from shutil import copyfile


class FileTester(object):

    testdir = 'tests/files/'

    testfile = testdir + 'test.ledger'
    sortedfile = testdir + 'test-already-sorted.ledger'
    alpha_unsortedfile = testdir + 'test-alpha-unsorted.ledger'
    alpha_sortedfile = testdir + 'test-alpha-sorted.ledger'
    readonlyfile = testdir + 'test-read-only.ledger'

    testschedulefile = testdir + 'test-schedule.ldg'
    testschedulefileafter = testdir + 'test-schedule-after.ldg'
    testschedulefileledger = testdir + 'test-schedule.ledger'

    mainfile = 'ledgerbil.py'

    @staticmethod
    def createTempFile(testdata):
        tempfile = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        return tempfile

    @staticmethod
    def copyToTempFile(filename):
        tempfile = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        copyfile(filename, tempfile)
        return tempfile

    @staticmethod
    def readFile(filename):
        f = open(filename, 'r')
        testdata = f.read()
        f.close()
        return testdata

    @staticmethod
    def writeToTempFile(filename, testdata):
        tempfile = filename + '_temp'
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        return tempfile
