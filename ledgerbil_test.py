#!/usr/bin/python

'''unit test for ledgerbil.py'''

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest
import os
import sys
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
        known_result = open('test.ledger', 'r').read()
        lbil = ledgerbil.Ledgerbil()
        lbil.parsefile(open('test.ledger', 'r'))
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

if __name__ == "__main__":
    unittest.main()
    
