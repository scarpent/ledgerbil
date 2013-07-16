#!/usr/bin/python

"""unit tests for ledgerbil.py"""

__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'

from unittest import TestCase
import sys
from os import remove

import ledgerbil
from filetester import FileTester as FT


class MainBasicInput(TestCase):

    def testMainNoOptionsOnSortedFile(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_sortedfile)
        sys.argv = [FT.mainfile, '--file', tempfile]
        ledgerbil.main()
        actual = FT.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

    def testMainNoOptionsOnUnsortedFile(self):
        """main should parse and write unsorted file unchanged"""
        expected = FT.readFile(FT.alpha_unsortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_unsortedfile)
        sys.argv = [FT.mainfile, '--file', tempfile]
        ledgerbil.main()
        actual = FT.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


class Sorting(TestCase):

    def testMainSortOnSortedFile(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_sortedfile)
        sys.argv = [FT.mainfile, '--file', tempfile, '--sort']
        ledgerbil.main()
        actual = FT.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

    def testMainSortedNoOptions(self):
        """main should parse unsorted file and write sorted file"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_unsortedfile)
        sys.argv = [FT.mainfile, '--file', tempfile, '--sort']
        ledgerbil.main()
        actual = FT.readFile(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


# todo: test for date stuff

# class Scheduling(TestCase):
#
#     def testMainWithScheduleFileOption(self):
#         """main should add scheduled items to ledger file"""


if __name__ == "__main__":
    unittest.main()         # pragma: no cover
