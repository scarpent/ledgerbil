#!/usr/bin/python

"""unit test for ledgerfile.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from unittest import TestCase
from os import remove
from os import chmod

from ledgerfile import LedgerFile
from ledgerthing import LedgerThing
from redirector import Redirector
from filetester import FileTester


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

    # todo:
    #       may have to revisit someday if some files are
    #       reference only and not opened for writing
    def testReadOnlyFile(self):
        """should fail with 'Permission denied'"""
        expected = "error: [Errno 13] Permission denied:"
        chmod(FileTester.readonlyfile, 0444)
        try:
            # file is opened for reading and writing, causing an error
            # immediately upon open if it is read only
            LedgerFile(FileTester.readonlyfile)
        except SystemExit:
            pass
        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)


class FileParsingOnInit(Redirector):

    def testParsedFileUnchangedViaPrint(self):
        """file output after parsing should be identical to input file"""
        expected = FileTester.readFile(FileTester.testfile)
        ledgerfile = LedgerFile(FileTester.testfile)
        ledgerfile.printFile()
        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())

    def testParsedFileUnchangedViaWrite(self):
        """file output after parsing should be identical to input file"""
        expected = FileTester.readFile(FileTester.testfile)
        tempfile = FileTester.copyToTempFile(FileTester.testfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.writeFile()
        actual = FileTester.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


class ThingCounting(TestCase):

    def testCountInitialNonTransaction(self):
        """counts initial non-transaction (probably a comment)"""
        testdata = '''; blah
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        tempfile = FileTester.createTempFile(testdata)
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
        tempfile = FileTester.createTempFile(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ledgerfile.thingCounter)

    def testAssignedThingNumbers(self):
        """thing numbers added in sequence starting at one"""
        testdata = '''; blah
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        tempfile = FileTester.createTempFile(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)

        thinglines = [
            '2011/01/01 beezlebub',
            '    assets: soul',
            '    liabilities: credit card  $666',
        ]
        thing = LedgerThing(thinglines)
        ledgerfile.addThing(thing)
        expected = '012'
        actual = ''
        for thing in ledgerfile.getThings():
            actual += str(thing.thingNumber)

        self.assertEquals(actual, expected)


class ThingDating(TestCase):

    def testInitialNonTransactionDate(self):
        """when 1st thing in file is a non-transaction, it has default date"""
        tempfile = FileTester.createTempFile('blah\nblah blah blah')
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()  # for now non-transaction dates are only populated
                        # with sort; may have to revisit this..
        remove(tempfile)
        self.assertEqual(
            LedgerFile.STARTING_DATE,
            ledgerfile.getThings()[0].thingDate
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
        tempfile = FileTester.createTempFile(testdata)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile._addThingLines(thingLines)
        ledgerfile.sort()  # for now non-transaction dates are only populated
                        # with sort; may have to revisit this..
        remove(tempfile)
        self.assertEqual(
            ledgerfile.getThings()[1].thingDate,
            ledgerfile.getThings()[2].thingDate
        )


class Sorting(TestCase):

    def testAlreadySortedFileUnchanged(self):
        """file output after sorting is identical to sorted input file"""
        expected = FileTester.readFile(FileTester.sortedfile)
        tempfile = FileTester.copyToTempFile(FileTester.sortedfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()
        ledgerfile.writeFile()
        actual = FileTester.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

    def testSorting(self):
        """test sorting"""
        expected = FileTester.readFile(FileTester.alpha_sortedfile)
        tempfile = FileTester.copyToTempFile(FileTester.alpha_unsortedfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()
        ledgerfile.writeFile()
        actual = FileTester.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

