#!/usr/bin/python

"""unit test for ledgerbil.py"""

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest
import sys
#from subprocess import Popen, PIPE
from StringIO import StringIO
import ledgerbil

testFile = 'test-very-small.ledger'


class Redirector(unittest.TestCase):

    def setUp(self):
        print('setted up')
        self.savestdout = sys.stdout
        self.redirect = StringIO()
        sys.stdout = self.redirect

    def tearDown(self):
        sys.stdout = self.savestdout
        print('teared down')


class ParseFileGoodInput(Redirector):

    def testParsedFileUnchanged(self):
        """file output after parsing should be identical to input file"""
        known_result = open(testFile, 'r').read()
        lbil = ledgerbil.Ledgerbil()
        lbil.parseFile(open(testFile, 'r'))
        lbil.printFile()
        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())


class MainBadInput(Redirector):

    def testMainBadFilename(self):
        """main should fail with 'No such file or directory'"""
        known_result = (
            "error: [Errno 2] No such file or directory: 'invalid.journal'\n"
        )
        ledgerbil.main(['ledgerbil.py', 'invalid.journal'])

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())


class MainGoodInput(Redirector):

    def testMainGoodFilename(self):
        """main should parse and print file, matching basic file read"""
        known_result = open(testFile, 'r').read()
        ledgerbil.main(['ledgerbil.py', testFile])

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())

    def ztestMainNoArgv(self):
        """main should use sys.argv if args not passed in"""
        known_result = open(testFile, 'r').read()
        sys.argv = ['ledgerbil.py', testFile]
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())

    def ztestMainStdin(self):
        """main should use stdin if file not passed in"""
        known_result = open(testFile, 'r').read()
        original_stdin = sys.stdin
        sys.stdin = open(testFile, 'r')
        ledgerbil.main(['ledgerbil.py'])
        sys.stdin = original_stdin

        self.redirect.seek(0)
        self.assertEqual(known_result, self.redirect.read())

if __name__ == "__main__":
    unittest.main()
