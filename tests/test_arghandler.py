#!/usr/bin/python

"""unit test for ledgerbil.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import sys
import unittest

from redirector import Redirector
from arghandler import ArgHandler

mainfile = 'dummy.py'
datafile = 'dummy.ldg'


# consider alternatives for command line tests: TextTestRunner,
# if name == 'main': unittest.main(exit=False)
# see: http://stackoverflow.com/questions/79754/unittest-causing-sys-exit
class Arguments(Redirector):

    def testFileOptionIsRequired(self):
        """should cause argparse error if file option not specified"""
        expected = 'error: argument -f/--file is required'
        sys.argv = [mainfile]
        try:
            ArgHandler.getArgs()
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testFileOptionAndFileBothRequired(self):
        """should cause argparse error if file opt specified w/o file"""
        expected = 'error: argument -f/--file: expected one argument'
        sys.argv = [mainfile, '--file']
        try:
            ArgHandler.getArgs()
        except SystemExit:
            pass

        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    def testFileShortOption(self):
        """should set parse args 'file' var"""
        sys.argv = [mainfile, '-f', datafile]
        args = ArgHandler.getArgs()
        self.assertTrue(args.file)

    def testFileLongOption(self):
        """should set parse args 'file' var"""
        sys.argv = [mainfile, '--file', datafile]
        args = ArgHandler.getArgs()
        self.assertTrue(args.file)

    def testSortShortOption(self):
        """should set parse args 'sort' var"""
        sys.argv = [mainfile, '-f', datafile, '-s']
        args = ArgHandler.getArgs()
        self.assertTrue(args.sort)

    def testSortLongOption(self):
        """should set parse args 'sort' var"""
        sys.argv = [mainfile, '--file', datafile, '--sort']
        args = ArgHandler.getArgs()
        self.assertTrue(args.sort)

    def testNoSortingOption(self):
        """should not set parse args 'sort' var"""
        sys.argv = [mainfile, '--file', datafile]
        args = ArgHandler.getArgs()
        self.assertFalse(args.sort)


if __name__ == "__main__":
    unittest.main()         # pragma: no cover
