#!/usr/bin/python

"""unit tests for ledgerbil.py"""

import os
import sys

from datetime import date
from dateutil.relativedelta import relativedelta
from unittest import TestCase

import ledgerbil

from filetester import FileTester as FT
from ledgerthing import LedgerThing


__author__ = 'scarpent'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class MainBasicInput(TestCase):

    def testMainNoOptionsOnSortedFile(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_sortedfile)
        ledgerbil.main(['--file', tempfile])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)

    def testMainNoOptionsOnUnsortedFile(self):
        """main should parse and write unsorted file unchanged"""
        expected = FT.readFile(FT.alpha_unsortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_unsortedfile)
        ledgerbil.main(['--file', tempfile])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)


class Sorting(TestCase):

    def testMainSortOnSortedFile(self):
        """main should parse and write sorted file unchanged"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_sortedfile)
        ledgerbil.main(['--file', tempfile, '--sort'])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)

    def testMainSortedNoOptions(self):
        """main should parse unsorted file and write sorted file"""
        expected = FT.readFile(FT.alpha_sortedfile)
        tempfile = FT.copyToTempFile(FT.alpha_unsortedfile)
        ledgerbil.main(['--file', tempfile, '--sort'])
        actual = FT.readFile(tempfile)
        os.remove(tempfile)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()         # pragma: no cover
