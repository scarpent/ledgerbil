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

testFile = 'tests/files/test.ledger'
mainFile = 'ledgerbil.py'


class Redirector(unittest.TestCase):

    def setUp(self):
        self.savestdout = sys.stdout
        self.redirect = StringIO()
        sys.stdout = self.redirect

    def tearDown(self):
        self.redirect.close()
        sys.stdout = self.savestdout


class ParseFileGoodInput(unittest.TestCase):

    def testParsedFileUnchanged(self):
        """file output after parsing should be identical to input file"""
        f = open(testFile, 'r')
        known_result = f.readlines()
        f.close()
        lbil = ledgerbil.Ledgerbil()
        f = open(testFile, 'r')
        lbil.parseFile(f)
        f.close()

        actual = lbil.getFileLines()
        self.assertEqual(known_result, actual)


class MainBadInput(Redirector):

    def testMainBadFilename(self):
        """main should fail with 'No such file or directory'"""
        known_result = (
            "error: [Errno 2] No such file or directory: 'invalid.journal'\n"
        )
        ledgerbil.main([mainFile, 'invalid.journal'])

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())
        self.redirect.truncate(0)


class MainGoodInput(Redirector):

    def testMainGoodFilename(self):
        """main should parse and print file, matching basic file read"""
        known_result = open(testFile, 'r').read()
        ledgerbil.main([mainFile, testFile])

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())
        self.redirect.truncate(0)

    def testMainNoArgv(self):
        """main should use sys.argv if args not passed in"""
        known_result = open(testFile, 'r').read()
        sys.argv = [mainFile, testFile]
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())
        self.redirect.truncate(0)

    def testMainStdin(self):
        """main should use stdin if file not passed in"""
        known_result = open(testFile, 'r').read()
        original_stdin = sys.stdin
        sys.stdin = open(testFile, 'r')
        ledgerbil.main([mainFile])
        sys.stdin = original_stdin

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())
        self.redirect.truncate(0)

if __name__ == "__main__":
    unittest.main()
