#!/usr/bin/python

"""unit test for ledgerfile.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import inspect


class FileTester():

    testdir = 'tests/files/'

    testfile = testdir + 'test.ledger'
    sortedfile = testdir + 'test-already-sorted.ledger'
    alpha_unsortedfile = testdir + 'test-alpha-unsorted.ledger'
    alpha_sortedfile = testdir + 'test-alpha-sorted.ledger'

    mainfile = 'ledgerbil.py'

    @staticmethod
    def getTempFilename():
        # gets the name of the calling function
        return FileTester.testdir + 'temp_' + inspect.stack()[1][3]

    @staticmethod
    def createTempFile(testdata):
        # includes the name of the calling function
        tempfile = FileTester.testdir + 'temp_' + inspect.stack()[1][3]
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        return tempfile

    @staticmethod
    def readFile(filename):
        f = open(filename, 'r')
        testdata = f.read()
        f.close()
        return testdata
