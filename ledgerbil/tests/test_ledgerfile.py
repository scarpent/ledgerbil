import sys
from os import remove
from textwrap import dedent
from unittest import TestCase, mock

import pytest

from .. import ledgerfile  # noqa (is used in patch)
from ..ledgerbilexceptions import LdgReconcilerError
from ..ledgerfile import LedgerFile
from ..ledgerthing import LedgerThing
from .filetester import FileTester
from .helpers import Redirector


@mock.patch(__name__ + '.ledgerfile.open')
@mock.patch(__name__ + '.ledgerfile.print')
def test_file_problem(mock_print, mock_open):
    mock_open.side_effect = IOError('fubar')
    with pytest.raises(SystemExit) as excinfo:
        LedgerFile('blarg')
    assert str(excinfo.value) == '-1'
    mock_print.assert_called_once_with('error: fubar', file=sys.stderr)
    mock_open.assert_called_once_with('blarg', 'r+')


class FileParsingOnInit(Redirector):

    def test_parsed_file_unchanged_via_print(self):
        """file output after parsing should be identical to input"""
        expected = FileTester.read_file(FileTester.testfile)
        lfile = LedgerFile(FileTester.testfile)
        lfile.print_file()
        self.redirect.seek(0)
        self.assertEqual(expected, self.redirect.read())
        self.assertIsNone(lfile.rec_account_matched)

    def test_parsed_file_unchanged_via_write(self):
        """file output after parsing should be identical to input"""
        expected = FileTester.read_file(FileTester.testfile)
        tempfile = FileTester.copy_to_temp_file(FileTester.testfile)
        lfile = LedgerFile(tempfile)
        lfile.write_file()
        actual = FileTester.read_file(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


class ThingCounting(TestCase):

    def test_count_initial_non_transaction(self):
        """counts initial non-transaction (probably a comment)"""
        testdata = dedent('''\
            ; blah
            ; blah blah blah
            2013/05/06 payee name
                expenses: misc
                liabilities: credit card  $-50
        ''')
        tempfile = FileTester.create_temp_file(testdata)
        lfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEqual(2, lfile.thing_counter)

    def test_count_initial_transaction(self):
        testdata = dedent('''\
            2013/05/06 payee name
                expenses: misc
                liabilities: credit card  $-50
            ; blah blah blah
            2013/05/06 payee name
                expenses: misc
                liabilities: credit card  $-50
            2013/02/30 invalid date (bonus test for thing date checking cov)
                (will be lumped with previous; note is invalid ledger file...)
            ''')
        tempfile = FileTester.create_temp_file(testdata)
        lfile = LedgerFile(tempfile)
        remove(tempfile)
        self.assertEqual(2, lfile.thing_counter)

    def test_assigned_thing_numbers(self):
        """thing numbers added in sequence starting at one"""
        testdata = dedent('''\
            ; blah
            ; blah blah blah
            2013/05/06 payee name
                expenses: misc
                liabilities: credit card  $-50
        ''')
        tempfile = FileTester.create_temp_file(testdata)
        lfile = LedgerFile(tempfile)
        remove(tempfile)

        thing = LedgerThing([
            '2011/01/01 beezlebub',
            '    assets: soul',
            '    liabilities: credit card  $666',
        ])
        lfile.add_thing(thing)
        expected = '012'
        actual = ''
        for thing in lfile.get_things():
            actual += str(thing.thing_number)

        self.assertEqual(actual, expected)


class ThingDating(TestCase):

    def test_initial_non_transaction_date(self):
        """1st thing in file is a non-transaction, has default date"""
        tempfile = FileTester.create_temp_file('blah\nblah blah blah')
        lfile = LedgerFile(tempfile)
        # non-transaction dates are only populated with sort
        lfile.sort()
        remove(tempfile)
        self.assertEqual(
            LedgerFile.STARTING_DATE,
            lfile.get_things()[0].thing_date
        )

    def test_later_non_transaction_date(self):
        """later non-transaction things inherit preceding thing date"""
        testdata = dedent('''\
            2013/05/06 payee name
                expenses: misc
                liabilities: credit card  $-1
            2013/05/07 payee name
                expenses: misc
                liabilities: credit card  $-2
            ''')
        tempfile = FileTester.create_temp_file(testdata)
        lfile = LedgerFile(tempfile)
        lfile.add_thing_from_lines(
            ['; blah blah blah', '; and so on...']
        )
        # non-transaction dates are only populated with sort
        lfile.sort()
        remove(tempfile)
        self.assertEqual(
            lfile.get_things()[1].thing_date,
            lfile.get_things()[2].thing_date
        )


class Sorting(TestCase):

    def test_already_sorted_file_unchanged(self):
        """file output after sorting is identical to sorted input"""
        expected = FileTester.read_file(FileTester.sortedfile)
        tempfile = FileTester.copy_to_temp_file(FileTester.sortedfile)
        lfile = LedgerFile(tempfile)
        lfile.sort()
        lfile.write_file()
        actual = FileTester.read_file(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)

    def test_sorting(self):
        """test sorting"""
        expected = FileTester.read_file(FileTester.alpha_sortedfile)
        tempfile = FileTester.copy_to_temp_file(
            FileTester.alpha_unsortedfile
        )
        lfile = LedgerFile(tempfile)
        lfile.sort()
        lfile.write_file()
        actual = FileTester.read_file(tempfile)
        remove(tempfile)
        self.assertEqual(expected, actual)


def test_reconciler_multiple_matches_across_transactions():
    # individual checking transactions ok, but multiple across file
    with pytest.raises(LdgReconcilerError) as excinfo:
        LedgerFile(FileTester.test_rec_multiple_match, 'checking')
    expected = ('More than one matching account:\n'
                '    a: checking down\n    a: checking up')
    assert str(excinfo.value) == expected


def test_reconciler_multiple_matches_within_transaction():
    # multiple matches within a single transaction
    with pytest.raises(LdgReconcilerError) as excinfo:
        LedgerFile(FileTester.test_rec_multiple_match, 'cash')
    expected = ('More than one matching account:\n'
                '    a: cash in\n    a: cash out')
    assert str(excinfo.value) == expected
