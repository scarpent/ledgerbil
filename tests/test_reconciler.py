#!/usr/bin/env python

import os

from datetime import date
from dateutil.relativedelta import relativedelta
from unittest import TestCase

import reconciler
import util

from filetester import FileTester
from helpers import OutputFileTester
from helpers import Redirector
from ledgerfile import LedgerFile
from reconciler import Reconciler


__author__ = 'Scott Carpenter'
__license__ = 'gpl v3 or greater'
__email__ = 'scottc@movingtofreedom.org'


next_week = date.today() + relativedelta(weeks=1)
testdata = '''
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
'''.format(next_week=util.get_date_string(next_week))

Reconciler.CACHE_FILE = FileTester.CACHE_FILE_TEST
FileTester.delete_test_cache_file()


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
            'help',
            'aliases',
            'quit', 'q', 'EOF',
            'account',
            'list', 'l', 'll',
            'mark', 'm',
            'unmark', 'u', 'un',
            # 'statement', 'start', # do not test here (need raw_input)
            'finish', 'end'
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
            'help help',
            'help aliases',
            'help quit', 'help q', 'help EOF',
            'help list', 'help l', 'help ll',
            'help account',
            'help mark', 'help m',
            'help unmark', 'help u',
            'help start', 'help finish',
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


class DataTests(Redirector):

    def verify_equal_floats(self, float1, float2):
        self.assertEqual(
            '{:.2f}'.format(float1),
            '{:.2f}'.format(float2)
        )

    def test_init_things(self):
        with FileTester.temp_input(testdata) as tempfilename:
            ledgerfile = LedgerFile(tempfilename, 'cash')
            recon = Reconciler(ledgerfile)

        self.verify_equal_floats(-15, recon.total_cleared)
        self.verify_equal_floats(-32.12, recon.total_pending)
        payees = {
            thing.payee for thing in recon.open_transactions
        }
        # all open transactions, including the future:
        self.assertEqual(
            ({'two', 'two pt five', 'three', 'four'}),
            payees
        )
        # noinspection PyCompatibility
        payees = {
            thing.payee for k, thing in
            recon.current_listing.iteritems()
            }
        # future items included only if pending ('three')
        self.assertEqual(
            ({'two', 'two pt five', 'three'}),
            payees
        )
        self.assertEqual(date.today(), recon.ending_date)
        self.assertIsNone(recon.ending_balance)
        self.assertEqual(3, len(recon.current_listing))
        self.assertEqual(
            'a: cash',
            ledgerfile.get_reconciliation_account()
        )

    def test_list(self):
        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        recon.do_list('')
        # noinspection PyCompatibility
        payees = {
            thing.payee for k, thing in
            recon.current_listing.iteritems()
        }
        # future items included only if pending ('three')
        self.assertEqual(
            ({'two', 'two pt five', 'three'}),
            payees
        )
        self.verify_equal_floats(-15, recon.total_cleared)
        self.verify_equal_floats(-32.12, recon.total_pending)

    def test_list_and_modify(self):

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-32.12, recon.total_pending)
            recon.do_list('')
            # noinspection PyCompatibility
            payees = {
                thing.payee for k, thing in
                recon.current_listing.iteritems()
                }
            self.assertEqual(
                ({'two', 'two pt five', 'three'}),
                payees
            )
            recon.do_unmark('3')

        # 3 was a pending future transaction, so:
        # pending total is adjusted and one less current listing
        # (also, the mark should have triggered a new listing...)
        # noinspection PyCompatibility
        payees = {
            thing.payee for k, thing in
            recon.current_listing.iteritems()
            }
        self.assertEqual(({'two', 'two pt five'}), payees)
        self.verify_equal_floats(-15, recon.total_cleared)
        self.verify_equal_floats(-2.12, recon.total_pending)

        # open transactions shouldn't change
        payees = {
            thing.payee for thing in recon.open_transactions
        }
        self.assertEqual(
            ({'two', 'two pt five', 'three', 'four'}),
            payees
        )

    def test_mark_and_unmark(self):

        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-32.12, recon.total_pending)
            recon.do_mark('1')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-52.12, recon.total_pending)
            recon.do_unmark('1 2')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-30, recon.total_pending)
            recon.do_mark('1 2')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-52.12, recon.total_pending)
            recon.do_unmark('2')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-50, recon.total_pending)
            recon.do_mark('1 2 blurg')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-52.12, recon.total_pending)
            recon.do_unmark('blarg 2')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-50, recon.total_pending)
            recon.do_unmark('1 sdjfkljsdfkljsdl 2')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-30, recon.total_pending)
            recon.default('1')
            self.verify_equal_floats(-15, recon.total_cleared)
            self.verify_equal_floats(-50, recon.total_pending)

        # entry with account on multiple lines
        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'credit'))

            self.verify_equal_floats(0, recon.total_cleared)
            self.verify_equal_floats(0, recon.total_pending)
            recon.do_mark('1')
            self.verify_equal_floats(0, recon.total_cleared)
            self.verify_equal_floats(-33, recon.total_pending)
            recon.do_unmark('1')
            self.verify_equal_floats(0, recon.total_cleared)
            self.verify_equal_floats(0, recon.total_pending)

    def test_finish_balancing_with_errors(self):
        """Verify things don't change when there are errors"""
        with FileTester.temp_input(testdata) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            recon.finish_balancing()

            payees = {
                thing.payee for thing in recon.open_transactions
                }
            self.assertEqual(
                ({'two', 'two pt five', 'three', 'four'}),
                payees
            )
            # noinspection PyCompatibility
            payees = {
                thing.payee for k, thing in
                recon.current_listing.iteritems()
                }
            # future items included only if pending ('three')
            self.assertEqual(
                ({'two', 'two pt five', 'three'}),
                payees
            )

            recon.ending_balance = -1234.56
            recon.finish_balancing()

            self.assertEqual(-1234.56, recon.ending_balance)
            payees = {
                thing.payee for thing in recon.open_transactions
                }
            self.assertEqual(
                ({'two', 'two pt five', 'three', 'four'}),
                payees
            )
            # noinspection PyCompatibility
            payees = {
                thing.payee for k, thing in
                recon.current_listing.iteritems()
                }
            # future items included only if pending ('three')
            self.assertEqual(
                ({'two', 'two pt five', 'three'}),
                payees
            )


class MockRawInput(TestCase):
    responses = []

    def mock_raw_input(self, prompt):
        assert self.responses
        response = self.responses.pop(0)
        print(prompt + response)
        return response

    def setUp(self):
        super(MockRawInput, self).setUp()
        self.save_raw_input = raw_input
        reconciler.raw_input = self.mock_raw_input

        Reconciler.CACHE_FILE = FileTester.CACHE_FILE_TEST
        FileTester.delete_test_cache_file()

    def tearDown(self):
        super(MockRawInput, self).tearDown()
        reconciler.raw_input = self.save_raw_input

        Reconciler.CACHE_FILE = FileTester.CACHE_FILE_TEST
        FileTester.delete_test_cache_file()


class StatementAndFinishTests(MockRawInput, OutputFileTester):

    def setUp(self):
        super(StatementAndFinishTests, self).setUp()

        # monkey patch date so it will be 10/27/2016
        class FixedDate(date):
            @classmethod
            def today(cls):
                return cls(2016, 10, 27)

        reconciler.date = FixedDate

    def tearDown(self):
        super(StatementAndFinishTests, self).tearDown()
        reconciler.date = date

    teststmt = '''
2016/10/26 one
    e: blurg
    a: cash         $-10

2016/10/29 two
    e: blurgerber
    a: cash         $-20
'''

    testfinish = '''
2016/10/26 one
    e: blurg
  * a: cash         $-10

2016/10/29 two
    e: blurgerber
  * a: cash         $-20
'''

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


class ResponseTests(MockRawInput, Redirector):

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


class CacheTests(MockRawInput, Redirector):

    testcache = '''
2016/10/26 one
    e: blurg
    a: cash         $-10

2016/10/26 two
    e: blurg
    a: credit       $-10
'''

    def test_get_key_and_cache_no_cache(self):

        assert not os.path.exists(FileTester.CACHE_FILE_TEST)

        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        assert not os.path.exists(FileTester.CACHE_FILE_TEST)

        key, cache = recon.get_key_and_cache()
        self.assertEqual('a: cash', key)
        self.assertEqual({}, cache)

    def test_get_key_and_cache_error(self):

        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()
        with open(Reconciler.CACHE_FILE, 'w') as cache_file:
            cache_file.write('bad json data')
        key, cache = recon.get_key_and_cache()
        self.assertEqual('a: cash', key)
        self.assertEqual({}, cache)
        self.assertEqual(
            'Error getting reconciler cache: '
            'No JSON object could be decoded.',
            self.redirect.getvalue().rstrip()
        )
        # not going to test file access since handled essentially the
        # same and don't want to bother with it

    def test_save_cache_error(self):

        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()
        Reconciler.CACHE_FILE = '/not/a/real/path/dDFgMAEVRPcjMZ'
        recon.save_statement_info_to_cache()
        self.assertEqual(
            "Error writing reconciler cache: [Errno 2] No such file "
            "or directory: '/not/a/real/path/dDFgMAEVRPcjMZ'",
            self.redirect.getvalue().rstrip()
        )
        # not going to test json ValueError because seems it would be
        # extremely unlikely given a valid cache dictionary

    def test_cache(self):

        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        # saving cache with ending balance "None" causes cache entry to
        # be removed; first let's make sure it works w/o existing entry
        assert not os.path.exists(FileTester.CACHE_FILE_TEST)
        assert recon.ending_balance is None
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        self.assertEqual({}, cache)

        # add entry
        recon.ending_balance = 100
        recon.ending_date = date(2020, 10, 20)
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        self.assertEqual(
            {u'a: cash': {
                u'ending_balance': 100,
                u'ending_date': u'2020/10/20'
            }},
            cache
        )

        # remove entry
        recon.ending_balance = None
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        self.assertEqual({}, cache)

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
            {u'a: credit': {
                u'ending_balance': 222,
                u'ending_date': u'2222/02/22'
            }, u'a: cash': {
                u'ending_balance': 111,
                u'ending_date': u'2111/11/11'
            }},
            cache
        )

        # remove credit
        recon.ending_balance = None
        recon.save_statement_info_to_cache()
        key, cache = recon.get_key_and_cache()
        self.assertEqual(
            {u'a: cash': {
                u'ending_balance': 111,
                u'ending_date': u'2111/11/11'
            }},
            cache
        )

        # indirectly verify get_statement_info_from_cache
        with FileTester.temp_input(self.testcache) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

        # get_statement_info_from_cache will have been called in init
        self.assertEqual(111, recon.ending_balance)
        self.assertEqual(date(2111, 11, 11), recon.ending_date)
