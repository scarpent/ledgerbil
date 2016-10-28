#!/usr/bin/env python

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
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

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
        self.assertEqual(date.today(), recon.to_date)
        self.assertIsNone(recon.ending_balance)
        self.assertEqual(3, len(recon.current_listing))

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
            recon.do_list('')
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

    def tearDown(self):
        super(MockRawInput, self).tearDown()
        reconciler.raw_input = self.save_raw_input


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

    def test_finish(self):
        self.init_test('test_reconcile_finish')

        with FileTester.temp_input(self.teststmt) as tempfilename:
            recon = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.responses = ['2016/10/30', '-30']
            recon.do_statement('')
            recon.do_mark('1 2')
            recon.do_finish('')

        self.conclude_test(strip_ansi_color=True)
