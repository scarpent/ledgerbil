#!/usr/bin/python

'''unit test for ledgerbil.py'''

from __future__ import print_function

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest
import sys
from subprocess import Popen, PIPE
from StringIO import StringIO
import ledgerbil

class Redirector(unittest.TestCase):

    def setUp(self):
        self.savestdout = sys.stdout
        self.redirect = StringIO()
        sys.stdout = self.redirect

    def tearDown(self):
        sys.stdout = self.savestdout

class ParseFileGoodInput(Redirector):

    def testParsedFileUnchanged(self):
        '''file output after parsing should be identical to input file'''
        known_result = open('test-small.ledger', 'r').read()
        lbil = ledgerbil.Ledgerbil()
        lbil.parsefile(open('test-small.ledger', 'r'))
        lbil.printfile()
        self.redirect.seek(0)
        self.assertEqual(self.redirect.read(), known_result)

class MainBadInput(Redirector):

    def testMainBadFilename(self):
        '''main should fail with "No such file or directory"'''
        known_result = (
            "error: [Errno 2] No such file or directory: 'invalid.journal'\n"
        )
        ledgerbil.main(['ledgerbil.py', 'invalid.journal'])

        self.redirect.seek(0)
        self.assertEqual(self.redirect.read(), known_result)

class MainGoodInput(Redirector):

    def testMainGoodFilename(self):
        '''main should parse and print file, matching basic file read'''
        known_result = open('test-small.ledger', 'r').read()
        ledgerbil.main(['ledgerbil.py', 'test-small.ledger'])

        self.redirect.seek(0)
        self.assertEqual(self.redirect.read(), known_result)

    def testMainNoArgv(self):
        '''main should use sys.argv if args not passed in'''
        known_result = open('test-small.ledger', 'r').read()
        sys.argv = ['ledgerbil.py', 'test-small.ledger']
        ledgerbil.main()

        self.redirect.seek(0)
        self.assertEqual(self.redirect.read(), known_result)

    def testMainStdin(self):
        '''main should use stdin if file not passed in'''
        known_result = open('test-small.ledger', 'r').read()
        original_stdin = sys.stdin
        sys.stdin = open('test-small.ledger', 'r')
        ledgerbil.main(['ledgerbil.py'])
        sys.stdin = original_stdin

        self.redirect.seek(0)
        self.assertEqual(self.redirect.read(), known_result)

if __name__ == "__main__":
    unittest.main()
