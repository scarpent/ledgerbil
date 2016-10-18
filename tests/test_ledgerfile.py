#!/usr/bin/python

"""unit test for ledgerfile.py"""

from unittest import TestCase
from os import remove
from os import chmod

from ledgerfile import LedgerFile
from ledgerthing import LedgerThing
from redirector import Redirector
from filetester import FileTester


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


class FileStuff(Redirector):

    def test_bad_filename(self):
        """should fail with 'No such file or directory'"""
        expected = "error: [Errno 2] No such file or directory:"
        try:
            LedgerFile('bad.filename')
        except SystemExit:
            pass
        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)

    # todo:
    #       may have to revisit someday if some files are
    #       reference only and not opened for writing
    def test_read_only_file(self):
        """should fail with 'Permission denied'"""
        expected = "error: [Errno 13] Permission denied:"
        chmod(FileTester.readonlyfile, 0o0444)
        try:
            # file is opened for reading and writing, causing an error
            # immediately upon open if it is read only
            LedgerFile(FileTester.readonlyfile)
        except SystemExit:
            pass
        self.redirecterr.seek(0)
        actual = self.redirecterr.read()
        self.assertTrue(expected in actual)


class FileParsingOnInit(Redirector):

    def test_parsed_file_unchanged_via_print(self):
        """file output after parsing should be identical to input"""
        expected = FileTester.read_file(FileTester.testfile)
        ledgerfile = LedgerFile(FileTester.testfile)
        ledgerfile.print_file()
        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())

    def test_parsed_file_unchanged_via_write(self):
        """file output after parsing should be identical to input"""
        expected = FileTester.read_file(FileTester.testfile)
        tempfile = FileTester.copy_to_temp_file(FileTester.testfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.write_file()
        actual = FileTester.read_file(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


class ThingCounting(TestCase):

    def test_count_initial_non_transaction(self):
        """counts initial non-transaction (probably a comment)"""
        testdata = '''; blah
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        tempfile = FileTester.create_temp_file(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ledgerfile.thingCounter)

    def test_count_initial_transaction(self):
        """counts initial transaction"""
        testdata = '''2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
2013/02/30 invalid date (bonus test for thing date checking coverage)
    (will be lumped with previous; note is invalid ledger file...)
'''
        tempfile = FileTester.create_temp_file(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEquals(2, ledgerfile.thingCounter)

    def test_assigned_thing_numbers(self):
        """thing numbers added in sequence starting at one"""
        testdata = '''; blah
; blah blah blah
2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-50
'''
        tempfile = FileTester.create_temp_file(testdata)
        ledgerfile = LedgerFile(tempfile)
        remove(tempfile)

        thinglines = [
            '2011/01/01 beezlebub',
            '    assets: soul',
            '    liabilities: credit card  $666',
        ]
        thing = LedgerThing(thinglines)
        ledgerfile.add_thing(thing)
        expected = '012'
        actual = ''
        for thing in ledgerfile.get_things():
            actual += str(thing.thingNumber)

        self.assertEquals(actual, expected)


class ThingDating(TestCase):

    def test_initial_non_transaction_date(self):
        """1st thing in file is a non-transaction, has default date"""
        tempfile = FileTester.create_temp_file('blah\nblah blah blah')
        ledgerfile = LedgerFile(tempfile)
        # non-transaction dates are only populated with sort
        ledgerfile.sort()
        remove(tempfile)
        self.assertEqual(
            LedgerFile.STARTING_DATE,
            ledgerfile.get_things()[0].thingDate
        )

    def test_later_non_transaction_date(self):
        """later non-transaction things inherit preceding thing date"""
        testdata = '''2013/05/06 payee name
    expenses: misc
    liabilities: credit card  $-1
2013/05/07 payee name
    expenses: misc
    liabilities: credit card  $-2
'''
        thing_lines = ['; blah blah blah', '; and so on...']
        tempfile = FileTester.create_temp_file(testdata)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile._add_thing_lines(thing_lines)
        # non-transaction dates are only populated with sort
        ledgerfile.sort()
        remove(tempfile)
        self.assertEqual(
            ledgerfile.get_things()[1].thingDate,
            ledgerfile.get_things()[2].thingDate
        )


class Sorting(TestCase):

    def test_already_sorted_file_unchanged(self):
        """file output after sorting is identical to sorted input"""
        expected = FileTester.read_file(FileTester.sortedfile)
        tempfile = FileTester.copy_to_temp_file(FileTester.sortedfile)
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()
        ledgerfile.write_file()
        actual = FileTester.read_file(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

    def test_sorting(self):
        """test sorting"""
        expected = FileTester.read_file(FileTester.alpha_sortedfile)
        tempfile = FileTester.copy_to_temp_file(
            FileTester.alpha_unsortedfile
        )
        ledgerfile = LedgerFile(tempfile)
        ledgerfile.sort()
        ledgerfile.write_file()
        actual = FileTester.read_file(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)
