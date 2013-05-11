#!/usr/bin/python

"""unit test for ledgerbil.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest
import sys
#from subprocess import Popen, PIPE
from StringIO import StringIO
import ledgerbil

from thing import LedgerThing
from thingtester import ThingTester
from argtester import ArgTester

testdir = 'tests/files/'
testfile = testdir + 'test.ledger'
sortedfile = testdir + 'test-already-sorted.ledger'
alpha_unsortedfile = testdir + 'test-alpha-unsorted.ledger'
alpha_sortedfile = testdir + 'test-alpha-sorted.ledger'

mainfile = 'ledgerbil.py'


class Redirector(ThingTester):

    def setUp(self):
        super(Redirector, self).setUp()
        self.savestdout = sys.stdout
        self.redirect = StringIO()
        sys.stdout = self.redirect

    def tearDown(self):
        self.redirect.close()
        sys.stdout = self.savestdout


class ParseFileGoodInput(ThingTester):

    def testParsedFileUnchanged(self):
        """file output after parsing should be identical to input file"""
        f = open(testfile, 'r')
        expected = f.read().splitlines()
        f.close()
        args = ArgTester()
        lbil = ledgerbil.Ledgerbil(args)
        f = open(testfile, 'r')
        lbil.parseFile(f)
        f.close()

        actual = lbil.getFileLines()
        self.assertEqual(expected, actual)


class ParseLinesGoodInput(ThingTester):

    def testCountInitialNonTransaction(self):
        """counts initial non-transaction (probably a comment)"""
        lines = ['; blah',
                 '; blah blah blah',
                 '2013/05/06 payee name',
                 '    expenses: misc',
                 '    liabilities: credit card  $-50']
        args = ArgTester()
        lbil = ledgerbil.Ledgerbil(args)
        lbil.parseLines(lines)
        self.assertEquals(2, LedgerThing.thingCounter)

    def testCountInitialTransaction(self):
        """counts initial transaction"""
        lines = ['2013/05/06 payee name',
                 '    expenses: misc',
                 '    liabilities: credit card  $-50',
                 '; blah blah blah',
                 '2013/05/06 payee name',
                 '    expenses: misc',
                 '    liabilities: credit card  $-50']
        lbil = ledgerbil.Ledgerbil('')
        lbil.parseLines(lines)
        self.assertEquals(2, LedgerThing.thingCounter)


class Sorting(ThingTester):

    def testAlreadySortedFileUnchanged(self):
        """file output after sorting is identical to sorted input file"""
        f = open(sortedfile, 'r')
        expected = f.read().splitlines()
        f.close()
        args = ArgTester()
        args.sort = True
        lbil = ledgerbil.Ledgerbil(args)
        f = open(sortedfile, 'r')
        lbil.parseFile(f)
        lbil.sortThings()
        f.close()

        actual = lbil.getFileLines()
        self.assertEqual(expected, actual)

    def testSorting(self):
        """test sorting"""
        unsorted = [
            '; blah blah blah',
            '2013/05/11 payee name',
            '    expenses: misc',
            '    liabilities: credit card  $-110',
            '2013/05/05 payee name',
            '    expenses: misc',
            '    liabilities: credit card  $-50'
        ]
        expected = [
            '; blah blah blah',
            '2013/05/05 payee name',
            '    expenses: misc',
            '    liabilities: credit card  $-50',
            '2013/05/11 payee name',
            '    expenses: misc',
            '    liabilities: credit card  $-110'
        ]
        args = ArgTester()
        args.sort = True
        lbil = ledgerbil.Ledgerbil(args)
        lbil.parseLines(unsorted)
        lbil.sortThings()
        self.assertEqual(expected, lbil.getFileLines())


class MainBadInput(Redirector):

    def testMainBadFilename(self):
        """main should fail with 'No such file or directory'"""
        expected = (
            "error: [Errno 2] No such file or directory: 'invalid.journal'\n"
        )
        sys.argv = [mainfile, 'invalid.journal']
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())


class MainGoodInput(Redirector):

    def testMainGoodFilename(self):
        """main should parse and print file, matching basic file read"""
        expected = open(testfile, 'r').read()
        sys.argv = [mainfile, testfile]
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())


class MainArguments(Redirector):

    def testSortingShortOption(self):
        """main should sort if -s or --sort is passed in"""
        expected = open(alpha_sortedfile, 'r').read()
        sys.argv = [mainfile, '-s', alpha_unsortedfile]
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())

    def testSortingLongOption(self):
        """main should sort if -s or --sort is passed in"""
        expected = open(alpha_sortedfile, 'r').read()
        sys.argv = [mainfile, '--sort', alpha_unsortedfile]
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
