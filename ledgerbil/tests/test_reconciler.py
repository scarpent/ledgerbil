import os
import sys
from datetime import date
from textwrap import dedent
from unittest import TestCase, mock

import pytest
from dateutil.relativedelta import relativedelta

from .. import reconciler, util
from ..ledgerbilexceptions import LdgReconcilerError
from ..ledgerfile import LedgerFile
from ..reconciler import Reconciler
from .filetester import FileTester
from .helpers import OutputFileTesterStdout, Redirector

next_week = util.get_date_string(date.today() + relativedelta(weeks=1))
testdata = dedent(f'''\
    2016/10/01 flibble
        e: smurg
        a: credit       $-11
        a: credit       $-22

    2016/10/26 one
        e: blurg
      * a: cash         $-10

    2016/10/26 one point five
        e: blurg
      * a: cash         $-5

    2016/10/27 two
        e: meep
        a: cash         $-20

    2016/10/27 two pt five
        e: meep 2
      ! a: cash         $-2.12

    2016/10/27 two point zwib
        i: jsdklfjsdlkjflksdjfklsd
        a: checking     $550

    {next_week} three
        e: fweep
      ! a: cash         $-30

    {next_week} four
        e: snurp
        a: cash         $-40
    ''')


class MockSettings(object):

    RECONCILER_CACHE_FILE = FileTester.CACHE_FILE_TEST

    def __init__(self):
        FileTester.delete_test_cache_file()


def setup_module(module):
    reconciler.settings = MockSettings()


def teardown_module(module):
    FileTester.delete_test_cache_file()


def verify_equal_floats(float1, float2, decimals=2):
    assert f'{float1:.{decimals}f}' == f'{float2:.{decimals}f}'


class SimpleOutputTests(Redirector):

    def test_syntax_error(self):
        with FileTester.temp_input(testdata) as tempfilename:
            interpreter = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()
        bad_command = 'cthulu'
        interpreter.onecmd(bad_command)
        self.assertEqual(
            Reconciler.UNKNOWN_SYNTAX + bad_command,
            self.redirect.getvalue().rstrip()
        )

    def test_not_syntax_error(self):
        """ crudely verify basic commands """
        commands = [
            # 'statement', 'start', # do not test here (need input)
            'account',
            'aliases',
            'finish', 'end',
            'help',
            'list', 'l', 'll',
            'mark', 'm',
            'quit', 'q', 'EOF',
            'reload', 'r',
            'show', 's',
            'unmark', 'u', 'un',
        ]
        with FileTester.temp_input(testdata) as tempfilename:
            interpreter = Reconciler(LedgerFile(tempfilename, 'cash'))

            for c in commands:
                self.reset_redirect()
                interpreter.onecmd(c)
                self.assertFalse(
                    self.redirect.getvalue().startswith(
                        Reconciler.UNKNOWN_SYNTAX
                    )
                )

    def test_simple_help_check(self):
        commands = [
            'help account',
            'help aliases',
            'help help',
            'help list', 'help l', 'help ll',
            'help mark', 'help m',
            'help quit', 'help q', 'help EOF',
            'help reload', 'help r',
            'help show', 'help s',
            'help start', 'help finish',
            'help unmark', 'help u',
        ]
        with FileTester.temp_input(testdata) as tempfilename:
            interpreter = Reconciler(LedgerFile(tempfilename, 'cash'))

        for c in commands:
            self.reset_redirect()
            interpreter.onecmd(c)
            self.assertFalse(
                self.redirect.getvalue().startswith(Reconciler.NO_HELP)
            )


class OutputTests(Redirector):

    def setUp(self):
        super().setUp()
        reconciler.settings = MockSettings()

    def tearDown(self):
        super().setUp()
        FileTester.delete_test_cache_file()

    def test_mark_and_unmark_errors(self):

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()

        # none of these should result in a file write; we'll get out of
        # the context manager as an additional confirmation of this

        for command in [recon.do_mark, recon.do_unmark]:
            command('')
            self.assertEqual(
                '*** Transaction number(s) required',
                self.redirect.getvalue().rstrip()
            )
            self.reset_redirect()
            command('ahchew')
            self.assertEqual(
                'Transaction not found: ahchew',
                self.redirect.getvalue().rstrip()
            )
            self.reset_redirect()

        recon.do_list('')
        self.reset_redirect()

        recon.do_mark('2')
        self.assertEqual(
            'Already marked pending: 2',
            self.redirect.getvalue().rstrip()
        )
        self.reset_redirect()
        recon.do_unmark('1')
        self.assertEqual(
            "Not marked; can't unmark: 1",
            self.redirect.getvalue().rstrip()
        )

    def test_finish_balancing_errors(self):

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.reset_redirect()
            recon.finish_balancing()
            self.assertEqual(
                '*** Ending balance must be set in order to finish',
                self.redirect.getvalue().rstrip()
            )

            self.reset_redirect()
            recon.ending_balance = -1234.56
            recon.finish_balancing()
            self.assertEqual(
                '"To zero" must be zero in order to finish',
                self.redirect.getvalue().rstrip()
            )
            # confirms it didn't revert to None as on success
            self.assertEqual(-1234.56, recon.ending_balance)

    def test_show_transaction_errors(self):

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'checking'))

        self.reset_redirect()
        recon.show_transaction('')
        self.assertEqual(
            '*** Transaction number(s) required',
            self.redirect.getvalue().rstrip()
        )
        self.reset_redirect()
        recon.show_transaction('blah')
        self.assertEqual(
            'Transaction not found: blah',
            self.redirect.getvalue().rstrip()
        )

    def test_show_one_transaction(self):
        expected = dedent('''\

            2016/10/27 two
                e: meep
                a: cash         $-20''')

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()
        recon.show_transaction('1')
        assert self.redirect.getvalue().rstrip() == expected

    def test_show_two_transactions(self):
        expected = dedent('''\

            2016/10/27 two
                e: meep
                a: cash         $-20

            2016/10/27 two pt five
                e: meep 2
              ! a: cash         $-2.12''')

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()
        recon.show_transaction('1 2')
        assert self.redirect.getvalue().rstrip() == expected


def test_mixed_shares_and_non_shares_raises_exception():
    ledgerfile_data = dedent('''
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx
            i: investment: adjustment     $100,000
    ''')

    with FileTester.temp_input(ledgerfile_data) as tempfilename:
        with pytest.raises(LdgReconcilerError) as excinfo:
            Reconciler(LedgerFile(tempfilename, '401k: bonds'))

    expected = 'Unhandled shares with non-shares: "a: 401k: bonds idx"'
    assert str(excinfo.value) == expected


def test_mixed_symbols_raises_exception():
    ledgerfile_data = dedent('''
        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 qwrty @   $20.05
            i: investment: adjustment

        2017/11/28 zombie investments
            a: 401k: bonds idx            12.357 abcde @   $20.05
            i: investment: adjustment
    ''')

    with FileTester.temp_input(ledgerfile_data) as tempfilename:
        with pytest.raises(LdgReconcilerError) as excinfo:
            Reconciler(LedgerFile(tempfilename, '401k: bonds'))

    expected = ('Unhandled multiple symbols: "a: 401k: bonds idx": '
                "['abcde', 'qwrty']")
    assert str(excinfo.value) == expected


def test_init_things():
    with FileTester.temp_input(testdata) as tempfilename:
        ledgerfile = LedgerFile(tempfilename, 'cash')
        recon = Reconciler(ledgerfile)

    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-32.12, recon.total_pending)
    payees = {
        thing.payee for thing in recon.open_transactions
    }
    # all open transactions, including the future:
    assert payees == ({'two', 'two pt five', 'three', 'four'})
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    # future items included only if pending ('three')
    assert payees == ({'two', 'two pt five', 'three'})
    assert recon.ending_date == date.today()
    assert recon.ending_balance is None
    assert len(recon.current_listing) == 3
    assert ledgerfile.rec_account_matched == 'a: cash'


def test_list_all():
    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    recon.do_list('')
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    # future items included only if pending ('three')
    assert payees == ({'two', 'two pt five', 'three'})
    recon.do_list('aLL')
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    assert payees == ({'two', 'two pt five', 'three', 'four'})


def test_list():
    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    recon.do_list('')
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    # future items included only if pending ('three')
    assert payees == ({'two', 'two pt five', 'three'})
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-32.12, recon.total_pending)


def test_list_shares():
    ledgerfile_data = dedent('''
        2017/11/05 zombie investments
          ! a: 401k: big co 500 idx       1.555555 abcdx @   $81.02
            i: investment: adjustment

        2017/11/06 zombie investments
          ! a: 401k: big co 500 idx       1.666666 abcdx @   $82.50
            i: investment: adjustment

        2017/11/07 zombie investments
          * a: 401k: big co 500 idx       1.777777 abcdx @   $87.78
            i: investment: adjustment

        2017/11/09 zombie investments
          * a: 401k: big co 500 idx       2.123456 abcdx @   $88.98
            i: investment: adjustment

        2017/11/11 zombie investments
            a: 401k: big co 500 idx       2.181818 abcdx @   $89.29
            i: investment: adjustment

        2017/11/13 zombie investments
            a: 401k: big co 500 idx       3.123321 abcdx @   $90.11
            i: investment: adjustment
    ''')

    with FileTester.temp_input(ledgerfile_data) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, '401k: big co'))

    recon.do_list('')
    verify_equal_floats(3.901233, recon.total_cleared, decimals=6)
    verify_equal_floats(3.222221, recon.total_pending, decimals=6)


def test_list_and_modify():

    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-32.12, recon.total_pending)
    recon.do_list('')
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    assert payees == ({'two', 'two pt five', 'three'})
    recon.do_unmark('3')

    # 3 was a pending future transaction, so:
    # pending total is adjusted and one less current listing
    # (also, the mark should have triggered a new listing...)
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    assert payees == ({'two', 'two pt five'})
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-2.12, recon.total_pending)

    # open transactions shouldn't change
    payees = {thing.payee for thing in recon.open_transactions}
    assert payees == ({'two', 'two pt five', 'three', 'four'})


def test_mark_and_unmark():

    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-32.12, recon.total_pending)
    recon.do_mark('1')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-52.12, recon.total_pending)
    recon.do_unmark('1 2')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-30, recon.total_pending)
    recon.do_mark('1 2')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-52.12, recon.total_pending)
    recon.do_unmark('2')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-50, recon.total_pending)
    recon.do_mark('1 2 blurg')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-52.12, recon.total_pending)
    recon.do_unmark('blarg 2')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-50, recon.total_pending)
    recon.do_unmark('1 sdjfkljsdfkljsdl 2')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-30, recon.total_pending)
    recon.default('1')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-50, recon.total_pending)

    # entry with account on multiple lines
    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'credit'))

    verify_equal_floats(0, recon.total_cleared)
    verify_equal_floats(0, recon.total_pending)
    recon.do_mark('1')
    verify_equal_floats(0, recon.total_cleared)
    verify_equal_floats(-33, recon.total_pending)
    recon.do_unmark('1')
    verify_equal_floats(0, recon.total_cleared)
    verify_equal_floats(0, recon.total_pending)


def test_mark_and_unmark_all():

    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-32.12, recon.total_pending)
    recon.do_unmark('all')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(0, recon.total_pending)
    recon.do_mark('all')
    verify_equal_floats(-15, recon.total_cleared)
    verify_equal_floats(-22.12, recon.total_pending)


def test_finish_balancing_with_errors():
    """Verify things don't change when there are errors"""
    with FileTester.temp_input(testdata) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    recon.finish_balancing()

    payees = {thing.payee for thing in recon.open_transactions}
    assert payees == ({'two', 'two pt five', 'three', 'four'})
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    # future items included only if pending ('three')
    assert payees == ({'two', 'two pt five', 'three'})

    recon.ending_balance = -1234.56
    recon.finish_balancing()
    assert recon.ending_balance == -1234.56
    payees = {thing.payee for thing in recon.open_transactions}
    assert payees == ({'two', 'two pt five', 'three', 'four'})
    payees = {
        thing.payee for k, thing in
        recon.current_listing.items()
    }
    # future items included only if pending ('three')
    assert payees == ({'two', 'two pt five', 'three'})


class MockInput(TestCase):
    responses = []

    def mock_input(self, prompt):
        assert self.responses
        response = self.responses.pop(0)
        print((prompt + response))
        return response

    def setUp(self):
        super().setUp()
        self.save_input = input
        reconciler.input = self.mock_input

    def tearDown(self):
        super().tearDown()
        reconciler.input = self.save_input


class StatementAndFinishTests(MockInput, OutputFileTesterStdout):

    def setUp(self):
        super().setUp()

        # monkey patch date so it will be 10/27/2016
        class FixedDate(date):
            @classmethod
            def today(cls):
                return cls(2016, 10, 27)

        reconciler.date = FixedDate
        reconciler.settings = MockSettings()

    def tearDown(self):
        super().tearDown()
        reconciler.date = date
        FileTester.delete_test_cache_file()

    teststmt = dedent('''\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/29 two
            e: blurgerber
            a: cash         $-20
        ''')

    testfinish = dedent('''
        2016/10/26 one
            e: blurg
          * a: cash         $-10

        2016/10/29 two
            e: blurgerber
          * a: cash         $-20
        ''')

    teststmt_shares = dedent('''\
        2016/10/26 banana
            a: 401k: big co 500 idx     0.123456 abcdx @   $81.89
            i: investment: yargle

        2016/10/27 sweet potato
            a: 401k: big co 500 idx        2.111 abcdx @   $82.13
            i: investment: yargle
        ''')

    def test_setting_statement_date_and_balance(self):
        self.init_test('test_statement_stuff')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        # errors and no change
        self.responses = ['blurg', '', 'abc', '']
        recon.do_statement('')
        # new settings
        self.responses = ['2016/10/30', '40']
        recon.do_statement('')
        # use $ symbol, no change
        self.responses = ['2016/10/30', '$40']
        recon.do_statement('')

        self.conclude_test(strip_ansi_color=True)

    def test_setting_statement_shares(self):
        self.init_test('test_statement_stuff_for_shares')

        with FileTester.temp_input(self.teststmt_shares) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'big co'))

        self.responses = ['2016/10/30', '0.1234567']
        recon.do_statement('')
        # so we can verify rounding on the balance prompt
        self.responses = ['2016/10/30', '2.234456']
        recon.do_statement('')

        self.conclude_test(strip_ansi_color=True)

    def test_cancel_statement(self):
        self.init_test('test_cancel_statement_stuff')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.responses = ['2016/10/27', '50']
        recon.do_statement('')
        self.responses = ['cAnCeL']
        recon.do_statement('')
        self.assertIsNone(recon.ending_balance)
        print('<<< test: restart >>>')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.assertIsNone(recon.ending_balance)
        self.responses = ['2016/10/28', '40']
        recon.do_statement('')
        self.responses = ['2016/10/28', 'cancel']
        recon.do_statement('')
        self.assertIsNone(recon.ending_balance)

    def test_finish(self):
        self.init_test('test_reconcile_finish')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.responses = ['2016/10/30', '-30']
            recon.do_statement('')
            recon.do_mark('1 2')
            recon.do_finish('')

        self.conclude_test(strip_ansi_color=True)

    def test_finish_and_start_again(self):
        self.init_test('test_reconcile_finish_and_start_again')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.responses = ['2016/10/30', '-30']
            recon.do_statement('')
            recon.do_mark('1 2')
            recon.do_finish('')

        print('<<< test: reconcile again >>>')
        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.responses = ['2016/10/30', '-30']
            recon.do_statement('')
            recon.do_quit('')

        # To verify that previous_ entries remain
        print('<<< test: restart >>>')
        with FileTester.temp_input(self.testfinish) as tempfilename:
            Reconciler(LedgerFile(tempfilename, 'cash'))

        self.conclude_test(strip_ansi_color=True)

    def test_caching_with_quit(self):
        self.cache_test(do_quit=True)

    def test_caching_without_quit(self):
        """ same results if we don't quit """
        self.cache_test(do_quit=False)

    def cache_test(self, do_quit=True):
        self.init_test('test_reconciler_caching')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.responses = ['2030/03/30', '-30']
        recon.do_statement('')
        if do_quit:
            recon.do_quit('')
        print('<<< test: restart >>>')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))
            recon.do_mark('1 2')
            recon.do_finish('')

        if do_quit:
            recon.do_quit('')
        print('<<< test: restart >>>')

        with FileTester.temp_input(self.testfinish) as tempfilename:
            Reconciler(LedgerFile(tempfilename, 'cash'))

        self.conclude_test(strip_ansi_color=True)


class ResponseTests(MockInput, Redirector):

    def test_get_response_with_none(self):
        """ None should be preserve for no response"""
        self.responses = ['']
        self.assertIsNone(Reconciler.get_response('prompt', None))
        self.responses = ['']
        self.assertEqual('', Reconciler.get_response('prompt', ''))

    def test_get_response(self):
        self.responses = ['']
        self.assertEqual(
            'preserve old value',
            Reconciler.get_response('prompt', 'preserve old value')
        )
        self.responses = ['new value']
        self.assertEqual(
            'new value',
            Reconciler.get_response('prompt', 'old value')
        )


testcache = dedent('''\
    2016/10/26 one
        e: blurg
        a: cash         $-10
    ''')


def test_get_key_and_cache_no_cache():
    assert not os.path.exists(reconciler.settings.RECONCILER_CACHE_FILE)
    with FileTester.temp_input(testcache) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))
    assert not os.path.exists(reconciler.settings.RECONCILER_CACHE_FILE)

    key, cache = recon.get_key_and_cache()
    assert key == 'a: cash'
    assert cache == {}


@mock.patch(__name__ + '.reconciler.print')
def test_get_key_and_cache_error(mock_print):
    with FileTester.temp_input(testcache) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    with mock.patch(__name__ + '.reconciler.os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with mock.patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError('BLAH!')
            key, cache = recon.get_key_and_cache()
    expected = 'Error getting reconciler cache: BLAH!'
    mock_print.assert_called_with(expected, file=sys.stderr)
    assert key == 'a: cash'
    assert cache == {}


@mock.patch(__name__ + '.reconciler.print')
@mock.patch(__name__ + '.reconciler.Reconciler.get_key_and_cache')
def test_save_cache_error(mock_get_key_and_cache, mock_print):
    mock_get_key_and_cache.return_value = ('cash', {})
    with FileTester.temp_input(testcache) as tempfilename:
        recon = Reconciler(LedgerFile(tempfilename, 'cash'))

    with mock.patch('builtins.open') as mock_open:
        mock_open.side_effect = IOError('BOO!')
        recon.save_statement_info_to_cache()
    expected = 'Error writing reconciler cache: BOO!'
    mock_print.assert_called_with(expected, file=sys.stderr)


class CacheTests(MockInput, Redirector):

    def setUp(self):
        super().setUp()
        reconciler.settings = MockSettings()

    def tearDown(self):
        super().setUp()
        FileTester.delete_test_cache_file()

    testcache = dedent('''\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/26 two
            e: blurg
            a: credit       $-10
        ''')

    def test_cache(self):
        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        # saving cache with ending balance "None" causes cache "ending_"
        # entries to be removed; first let's make sure it works w/o
        # existing entry
        assert not os.path.exists(reconciler.settings.RECONCILER_CACHE_FILE)
        assert recon.ending_balance is None
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        assert cache == {}

        # add entry
        recon.ending_balance = 100
        recon.ending_date = date(2020, 10, 20)
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        self.assertEqual(
            {'a: cash': {
                'ending_balance': 100,
                'ending_date': '2020/10/20'
            }},
            cache
        )

        # remove entry
        recon.ending_balance = None
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        assert cache == {'a: cash': {}}

        # multiple entries
        recon.ending_balance = 111
        recon.ending_date = date(2111, 11, 11)
        recon.save_statement_info_to_cache()

        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'credit'))

        recon.ending_balance = 222
        recon.ending_date = date(2222, 2, 22)
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        self.assertEqual(
            {'a: credit': {
                'ending_balance': 222,
                'ending_date': '2222/02/22'
            }, 'a: cash': {
                'ending_balance': 111,
                'ending_date': '2111/11/11'
            }},
            cache
        )

        # remove credit
        recon.ending_balance = None
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        expected = {
            'a: cash': {
                'ending_balance': 111,
                'ending_date': '2111/11/11'
            },
            'a: credit': {}
        }
        assert cache == expected

        # indirectly verify get_statement_info_from_cache
        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        # get_statement_info_from_cache will have been called in init
        self.assertEqual(111, recon.ending_balance)
        self.assertEqual(date(2111, 11, 11), recon.ending_date)


class ReloadTests(TestCase):

    def setUp(self):
        super().setUp()
        reconciler.settings = MockSettings()

    def tearDown(self):
        super().setUp()
        FileTester.delete_test_cache_file()

    testdata = dedent('''\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/29 two
            e: glarg
          * a: cash         $-20
        ''')

    testdata_modified = dedent('''\
        2016/10/26 one
            e: blurg
            a: cash         $-10

        2016/10/29 two
            e: blarg
          * a: cash         $-55
        ''')

    def test_reload(self):
        with FileTester.temp_input(self.testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))
            self.assertEqual(-20, recon.total_cleared)

            with open(tempfilename, 'w') as the_file:
                the_file.write(self.testdata_modified)

            self.assertEqual(-20, recon.total_cleared)
            recon.do_reload('')
            self.assertEqual(-55, recon.total_cleared)
