#!/usr/bin/python

"""unit tests for ledgerbil.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

import unittest
import sys
from os import remove

import ledgerbil
from filetester import FileTester as FT


class MainGoodInput(unittest.TestCase):

    def testMainGoodFilename(self):
        """main should parse and print file, matching basic file read"""
        expected = FT.readFile(FT.testfile)
        tempfile = FT.copyToTempFile(FT.testfile)
        sys.argv = [FT.mainfile, '--file', tempfile]
        ledgerbil.main()
        actual = FT.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


# consider alternatives for command line tests: TextTestRunner,
# if name == 'main': unittest.main(exit=False)
# see: http://stackoverflow.com/questions/79754/unittest-causing-sys-exit
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
