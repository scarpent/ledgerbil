#!/usr/bin/python

"""unit test for ledgerfile.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


import unittest
import inspect
from shutil import copyfile
from os import remove

import ledgerfile
from redirector import Redirector

testdir = 'tests/files/'
testfile = testdir + 'test.ledger'
testfile_copy = testdir + 'test.ledger.copy'
sortedfile = testdir + 'test-already-sorted.ledger'
alpha_unsortedfile = testdir + 'test-alpha-unsorted.ledger'
alpha_sortedfile = testdir + 'test-alpha-sorted.ledger'


def getTempFilename():
    # gets the name of the calling function
    return testdir + 'temp_' + inspect.stack()[1][3]


class LedgerFileInit(Redirector):

    def testParsedFileUnchangedViaPrint(self):
        """file output after parsing should be identical to input file"""
        f = open(testfile, 'r')
        expected = f.read()
        f.close()
        ldgfile = ledgerfile.LedgerFile(testfile)
        ldgfile.printFile()
        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())

    def testParsedFileUnchangedViaWrite(self):
        """file output after parsing should be identical to input file"""
        tempfile = getTempFilename()
        f = open(testfile, 'r')
        expected = f.read()
        f.close()
        copyfile(testfile, tempfile)
        ldgfile = ledgerfile.LedgerFile(tempfile)
        ldgfile.writeFile()
        f = open(tempfile, 'r')
        actual = f.read()
        f.close()
        remove(tempfile)
        self.assertEqual(expected, actual)

    def testCountInitialNonTransaction(self):
        """counts initial non-transaction (probably a comment)"""
        tempfile = getTempFilename()
        testdata = '''; blah
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        ldgfile = ledgerfile.LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ldgfile.thingCounter)

    def testCountInitialTransaction(self):
        """counts initial transaction"""
        tempfile = getTempFilename()
        testdata = '''2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        f = open(tempfile, 'w')
        f.write(testdata)
        f.close()
        ldgfile = ledgerfile.LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ldgfile.thingCounter)


class Sorting(unittest.TestCase):

    def testAlreadySortedFileUnchanged(self):
        """file output after sorting is identical to sorted input file"""
        tempfile = getTempFilename()
        f = open(sortedfile, 'r')
        expected = f.read()
        f.close()
        copyfile(sortedfile, tempfile)
        ldgfile = ledgerfile.LedgerFile(tempfile)
        ldgfile.sort()
        ldgfile.writeFile()
        f = open(tempfile, 'r')
        actual = f.read()
        f.close()
        remove(tempfile)
        self.assertEqual(expected, actual)

#     def testSorting(self):
#         """test sorting"""
#         unsorted = [
#             '; blah blah blah',
#             '2013/05/11 payee name',
#             '    expenses: misc',
#             '    liabilities: credit card  $-110',
#             '2013/05/05 payee name',
#             '    expenses: misc',
#             '    liabilities: credit card  $-50'
#         ]
#         expected = [
#             '; blah blah blah',
#             '2013/05/05 payee name',
#             '    expenses: misc',
#             '    liabilities: credit card  $-50',
#             '2013/05/11 payee name',
#             '    expenses: misc',
#             '    liabilities: credit card  $-110'
#         ]
#         args = ArgTester()
#         args.sort = True
#         lbil = ledgerbil.Ledgerbil(args)
#         lbil.parseLines(unsorted)
#         lbil.sortThings()
#         self.assertEqual(expected, lbil.getFileLines())
#
#
# class MainBadInput(Redirector):
#
#     def testMainBadFilename(self):
#         """main should fail with 'No such file or directory'"""
#         expected = (
#             "error: [Errno 2] No such file or directory: 'invalid.journal'\n"
#         )
#         sys.argv = [mainfile, '--file', 'invalid.journal']
#         ledgerbil.main()
#
#         self.redirect.seek(0)
#         self.assertEqual(expected, self.redirect.read())
#
#
# class MainGoodInput(Redirector):
#
#     def testMainGoodFilename(self):
#         """main should parse and print file, matching basic file read"""
#         expected = open(testfile, 'r').read()
#         sys.argv = [mainfile, '--file', testfile]
#         ledgerbil.main()
#
#         self.redirect.seek(0)
#         self.assertEqual(expected, self.redirect.read())
#
#
# # consider alternatives for command line tests: TextTestRunner,
# # if name == 'main': unittest.main(exit=False)
# # see: http://stackoverflow.com/questions/79754/unittest-causing-sys-exit
# class MainArguments(Redirector):
#
#     def testFileOptionIsRequired(self):
#         """main should cause argparse error if file option not specified"""
#         expected = 'ledgerbil.py: error: argument -f/--file is required'
#         sys.argv = [mainfile]
#         try:
#             ledgerbil.main()
#         except SystemExit:
#             pass
#
#         self.redirecterr.seek(0)
#         actual = self.redirecterr.read()
#         self.assertTrue(expected in actual)
#
#     def testFileOptionAndFileBothRequired(self):
#         """main should cause argparse error if file opt specified w/o file"""
#         expected = ('ledgerbil.py: error: argument -f/--file: ' +
#                     'expected one argument')
#         sys.argv = [mainfile, '--file']
#         try:
#             ledgerbil.main()
#         except SystemExit:
#             pass
#
#         self.redirecterr.seek(0)
#         actual = self.redirecterr.read()
#         self.assertTrue(expected in actual)
#
#     def testSortingShortOption(self):
#         """main should sort if -s specified (also tests --file long option)"""
#         expected = open(alpha_sortedfile, 'r').read()
#         sys.argv = [mainfile, '-s', '--file', alpha_unsortedfile]
#         ledgerbil.main()
#
#         self.redirect.seek(0)
#         self.assertEqual(expected, self.redirect.read())
#
#     def testSortingLongOption(self):
#         """main should sort if --sort is specified (also tests -f short opt"""
#         expected = open(alpha_sortedfile, 'r').read()
#         sys.argv = [mainfile, '--sort', '-f', alpha_unsortedfile]
#         ledgerbil.main()
#
#         self.redirect.seek(0)
#         self.assertEqual(expected, self.redirect.read())
#
#     def testNoSorting(self):
#         """file remains unsorted if sorting not specified"""
#         expected = open(alpha_unsortedfile, 'r').read()
#         sys.argv = [mainfile, '--file', alpha_unsortedfile]
#         ledgerbil.main()
#
#         self.redirect.seek(0)
#         self.assertEqual(expected, self.redirect.read())

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
