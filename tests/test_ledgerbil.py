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

testdir = 'tests/files/'
testfile = testdir + 'test.ledger'
sortedfile = testdir + 'test-already-sorted.ledger'

mainFile = 'ledgerbil.py'


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
        known_result = f.read().splitlines()
        f.close()
        lbil = ledgerbil.Ledgerbil()
        f = open(testfile, 'r')
        lbil.parseFile(f)
        f.close()

        actual = lbil.getFileLines()
        self.assertEqual(known_result, actual)

    def testAlreadySortedFileUnchanged(self):
        """file output after sorting is identical to sorted input file"""
        f = open(sortedfile, 'r')
        known_result = f.read().splitlines()
        f.close()
        lbil = ledgerbil.Ledgerbil()
        f = open(sortedfile, 'r')
        lbil.parseFile(f)
        lbil.sortThings()
        f.close()

        actual = lbil.getFileLines()
        self.assertEqual(known_result, actual)


class ParseLinesGoodInput(ThingTester):

    def testCountInitialNonTransaction(self):
        """counts initial non-transaction (probably a comment)"""
        lines = ['; blah',
                 '; blah blah blah',
                 '2013/05/06 payee name',
                 '    expenses: misc',
                 '    liabilities: credit card  $-50']
        lbil = ledgerbil.Ledgerbil()
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
        lbil = ledgerbil.Ledgerbil()
        lbil.parseLines(lines)
        self.assertEquals(2, LedgerThing.thingCounter)

class MainBadInput(Redirector):

    def testMainBadFilename(self):
        """main should fail with 'No such file or directory'"""
        known_result = (
            "error: [Errno 2] No such file or directory: 'invalid.journal'\n"
        )
        ledgerbil.main([mainFile, 'invalid.journal'])

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())


class MainGoodInput(Redirector):

    def testMainGoodFilename(self):
        """main should parse and print file, matching basic file read"""
        known_result = open(testfile, 'r').read()
        ledgerbil.main([mainFile, testfile])

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())

    def testMainNoArgv(self):
        """main should use sys.argv if args not passed in"""
        known_result = open(testfile, 'r').read()
        sys.argv = [mainFile, testfile]
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())

    def testMainStdin(self):
        """main should use stdin if file not passed in"""
        known_result = open(testfile, 'r').read()
        original_stdin = sys.stdin
        sys.stdin = open(testfile, 'r')
        ledgerbil.main([mainFile])
        sys.stdin = original_stdin

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())

if __name__ == "__main__":
    unittest.main()         # pragma: no cover
