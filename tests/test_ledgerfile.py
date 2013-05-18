#!/usr/bin/python

"""unit test for py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


import unittest
import inspect
from shutil import copyfile
from os import remove

from ledgerfile import LedgerFile
from redirector import Redirector

testdir = 'tests/files/'
testfile = testdir + 'test.ledger'
sortedfile = testdir + 'test-already-sorted.ledger'
alpha_unsortedfile = testdir + 'test-alpha-unsorted.ledger'
alpha_sortedfile = testdir + 'test-alpha-sorted.ledger'


class TestingFileHelper():

    @staticmethod
    def getTempFilename():
        # gets the name of the calling function
        return testdir + 'temp_' + inspect.stack()[1][3]

    @staticmethod
    def createTempFile(testdata):
        # includes the name of the calling function
        tempfile = testdir + 'temp_' + inspect.stack()[1][3]
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


class FileStuff(Redirector):

    def testBadFilename(self):
        """should fail with 'No such file or directory'"""
        expected = "error: [Errno 2] No such file or directory:"
        try:
            LedgerFile('bad.filename')
        except SystemExit:
            pass
        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)


class FileParsingOnInit(Redirector):

    def testParsedFileUnchangedViaPrint(self):
        """file output after parsing should be identical to input file"""
        expected = TestingFileHelper.readFile(testfile)
        ledgerfile = LedgerFile(testfile)
        ledgerfile.printFile()
        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())

    def testParsedFileUnchangedViaWrite(self):
        """file output after parsing should be identical to input file"""
        expected = TestingFileHelper.readFile(testfile)
        tempfile = TestingFileHelper.getTempFilename()
        copyfile(testfile, tempfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.writeFile()
        actual = TestingFileHelper.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


class ThingCounting(unittest.TestCase):

    def testCountInitialNonTransaction(self):
        """counts initial non-transaction (probably a comment)"""
        testdata = '''; blah
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        tempfile = TestingFileHelper.createTempFile(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ledgerfile.thingCounter)

    def testCountInitialTransaction(self):
        """counts initial transaction"""
        testdata = '''2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
2013/02/30 invalid date (bonus test for thing date checking code coverage)
    (will be lumped with previous; note that this is invalid ledger file...)
'''
        tempfile = TestingFileHelper.createTempFile(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ledgerfile.thingCounter)


class ThingDating(unittest.TestCase):

    def testInitialNonTransactionDate(self):
        """when 1st thing in file is a non-transaction, it has default date"""
        tempfile = TestingFileHelper.createTempFile('blah\nblah blah blah')
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()  # for now non-transaction dates are only populated
                        # with sort; may have to revisit this..
        remove(tempfile)
        self.assertEqual(
            LedgerFile.STARTING_DATE,
            ledgerfile.getThings()[0].date
        )

    def testLaterNonTransactionDate(self):
        """later non-transaction things inherit date of preceding thing"""
        testdata = '''2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-1
2013/05/07 payee name
    expenses: misc
    liabilities: credit card  $-2
'''
        thingLines = ['; blah blah blah', '; and so on...']
        tempfile = TestingFileHelper.createTempFile(testdata)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile._addThingLines(thingLines)
        ledgerfile.sort()  # for now non-transaction dates are only populated
                        # with sort; may have to revisit this..
        remove(tempfile)
        self.assertEqual(
            ledgerfile.getThings()[1].date,
            ledgerfile.getThings()[2].date
        )


class Sorting(unittest.TestCase):

    def testAlreadySortedFileUnchanged(self):
        """file output after sorting is identical to sorted input file"""
        expected = TestingFileHelper.readFile(sortedfile)
        tempfile = TestingFileHelper.getTempFilename()
        copyfile(sortedfile, tempfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()
        ledgerfile.writeFile()
        actual = TestingFileHelper.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

    def testSorting(self):
        """test sorting"""
        expected = TestingFileHelper.readFile(alpha_sortedfile)
        tempfile = TestingFileHelper.getTempFilename()
        copyfile(alpha_unsortedfile, tempfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()
        ledgerfile.writeFile()
        actual = TestingFileHelper.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()         # pragma: no cover
