import datetime
import sys
from textwrap import dedent
from unittest import mock

import pytest

from . import filetester as FT
from .. import ledgerfile  # noqa: F401 (is used in patch)
from ..ledgerbilexceptions import LdgReconcilerError
from ..ledgerfile import LedgerFile
from ..ledgerthing import LedgerThing
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
        expected = FT.read_file(FT.testfile)
        lfile = LedgerFile(FT.testfile)
        lfile.print_file()
        self.redirect.seek(0)
        assert self.redirect.read() == expected
        assert lfile.rec_account_matched is None


def test_parsed_file_unchanged_via_write():
    """file output after parsing should be identical to input"""
    expected = FT.read_file(FT.testfile)
    with FT.temp_file(expected) as templedgerfile:
        lfile = LedgerFile(templedgerfile)
        lfile.write_file()
        actual = FT.read_file(templedgerfile)
    assert expected == actual


def test_count_initial_non_transaction():
    """counts initial non-transaction (probably a comment)"""
    testdata = dedent('''\
        ; blah
        ; blah blah blah
        2013/05/06 payee name
            expenses: misc
            liabilities: credit card  $-50
    ''')
    with FT.temp_file(testdata) as templedgerfile:
        lfile = LedgerFile(templedgerfile)

    assert lfile.thing_counter == 2


def test_count_initial_transaction():
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
    with FT.temp_file(testdata) as templedgerfile:
        lfile = LedgerFile(templedgerfile)

    assert lfile.thing_counter == 2


def test_assigned_thing_numbers():
    """thing numbers added in sequence starting at one"""
    testdata = dedent('''\
        ; blah
        ; blah blah blah
        2013/05/06 payee name
            expenses: misc
            liabilities: credit card  $-50
    ''')
    with FT.temp_file(testdata) as templedgerfile:
        lfile = LedgerFile(templedgerfile)

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

    assert expected == actual


def test_initial_non_transaction_date():
    """1st thing in file is a non-transaction, has default date"""
    with FT.temp_file('blah\nblah blah blah') as templedgerfile:
        lfile = LedgerFile(templedgerfile)

    # non-transaction dates are only populated with sort
    lfile.sort()
    assert lfile.get_things()[0].thing_date == LedgerFile.STARTING_DATE


def test_later_non_transaction_date():
    """later non-transaction things inherit preceding thing date"""
    testdata = dedent('''\
        2013/05/06 payee name
            expenses: misc
            liabilities: credit card  $-1
        2013/05/07 payee name
            expenses: misc
            liabilities: credit card  $-2
        ''')
    with FT.temp_file(testdata) as templedgerfile:
        lfile = LedgerFile(templedgerfile)

    lfile.add_thing_from_lines(['; blah blah blah', '; and so on...'])
    # non-transaction dates are only populated with sort
    lfile.sort()
    assert lfile.get_things()[0].thing_date == datetime.date(2013, 5, 6)
    assert lfile.get_things()[1].thing_date == datetime.date(2013, 5, 7)
    assert lfile.get_things()[2].thing_date == datetime.date(2013, 5, 7)


def test_already_sorted_file_unchanged():
    """file output after sorting is identical to sorted input"""
    expected = FT.read_file(FT.sortedfile)
    with FT.temp_file(expected) as templedgerfile:
        lfile = LedgerFile(templedgerfile)
        lfile.sort()
        lfile.write_file()
        actual = FT.read_file(templedgerfile)

    assert actual == expected


def test_sorting():
    expected = FT.read_file(FT.alpha_sortedfile)
    unsorted = FT.read_file(FT.alpha_unsortedfile)
    with FT.temp_file(unsorted) as templedgerfile:
        lfile = LedgerFile(templedgerfile)
        lfile.sort()
        lfile.write_file()
        actual = FT.read_file(templedgerfile)

    assert actual == expected


def test_reconciler_multiple_matches_across_transactions():
    # individual checking transactions ok, but multiple across file
    with pytest.raises(LdgReconcilerError) as excinfo:
        LedgerFile(FT.test_rec_multiple_match, 'checking')
    expected = ('More than one matching account:\n'
                '    a: checking down\n    a: checking up')
    assert str(excinfo.value) == expected


def test_reconciler_multiple_matches_within_transaction():
    # multiple matches within a single transaction
    with pytest.raises(LdgReconcilerError) as excinfo:
        LedgerFile(FT.test_rec_multiple_match, 'cash')
    expected = ('More than one matching account:\n'
                '    a: cash in\n    a: cash out')
    assert str(excinfo.value) == expected
