#!/usr/bin/env python

from datetime import date
from dateutil.relativedelta import relativedelta
from unittest import TestCase

import reconciler
import util

from filetester import FileTester
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
            #'statement', 'start', # do not test here (need raw_input)
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
            reconciler = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.reset_redirect()

        # none of these should result in a file write; we'll get out of
        # the context manager as an additional confirmation of this

        for command in [reconciler.do_mark, reconciler.do_unmark]:
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

        reconciler.do_list('')
        self.reset_redirect()

        reconciler.do_mark('2')
        self.assertEqual(
            'Already marked pending: 2',
            self.redirect.getvalue().rstrip()
        )
        self.reset_redirect()
        reconciler.do_unmark('1')
        self.assertEqual(
            "Not marked; can't unmark: 1",
            self.redirect.getvalue().rstrip()
        )


class DataTests(Redirector):

    def verify_equal_floats(self, float1, float2):
        self.assertEqual(
            '{:.2f}'.format(float1),
            '{:.2f}'.format(float2)
        )

    def test_init_things(self):
        with FileTester.temp_input(testdata) as tempfilename:
            reconciler = Reconciler(LedgerFile(tempfilename, 'cash'))

        self.verify_equal_floats(-15, reconciler.total_cleared)
        self.verify_equal_floats(-32.12, reconciler.total_pending)
        payees = {
            thing.payee for thing in reconciler.open_transactions
        }
        # all open transactions, including the future:
        self.assertEqual(
            ({'two', 'two pt five', 'three', 'four'}),
            payees
        )
        self.assertEqual(date.today(), reconciler.to_date)
        self.assertIsNone(reconciler.ending_balance)
        self.assertEqual(3, len(reconciler.current_listing))

    def test_list(self):
        with FileTester.temp_input(testdata) as tempfilename:
            reconciler = Reconciler(LedgerFile(tempfilename, 'cash'))

        reconciler.do_list('')
        # noinspection PyCompatibility
        payees = {
            thing.payee for k, thing in
            reconciler.current_listing.iteritems()
        }
        # only future items should be pending items ('three')
        self.assertEqual(
            ({'two', 'two pt five', 'three'}),
            payees
        )
        self.verify_equal_floats(-15, reconciler.total_cleared)
        self.verify_equal_floats(-32.12, reconciler.total_pending)

    def test_list_and_modify(self):

        with FileTester.temp_input(testdata) as tempfilename:
            reconciler = Reconciler(LedgerFile(tempfilename, 'cash'))
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-32.12, reconciler.total_pending)
            reconciler.do_list('')
            # noinspection PyCompatibility
            payees = {
                thing.payee for k, thing in
                reconciler.current_listing.iteritems()
                }
            self.assertEqual(
                ({'two', 'two pt five', 'three'}),
                payees
            )
            reconciler.do_unmark('3')

        # 3 was a pending future transaction, so:
        # pending total is adjusted and one less current listing
        # (also, the mark should have triggered a new listing...)
        # noinspection PyCompatibility
        payees = {
            thing.payee for k, thing in
            reconciler.current_listing.iteritems()
            }
        self.assertEqual(({'two', 'two pt five'}), payees)
        self.verify_equal_floats(-15, reconciler.total_cleared)
        self.verify_equal_floats(-2.12, reconciler.total_pending)

        # open transactions shouldn't change
        payees = {
            thing.payee for thing in reconciler.open_transactions
        }
        self.assertEqual(
            ({'two', 'two pt five', 'three', 'four'}),
            payees
        )

    def test_mark_and_unmark(self):

        with FileTester.temp_input(testdata) as tempfilename:
            reconciler = Reconciler(LedgerFile(tempfilename, 'cash'))

            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-32.12, reconciler.total_pending)
            reconciler.do_list('')
            reconciler.do_mark('1')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-52.12, reconciler.total_pending)
            reconciler.do_unmark('1 2')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-30, reconciler.total_pending)
            reconciler.do_mark('1 2')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-52.12, reconciler.total_pending)
            reconciler.do_unmark('2')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-50, reconciler.total_pending)
            reconciler.do_mark('1 2 blurg')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-52.12, reconciler.total_pending)
            reconciler.do_unmark('blarg 2')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-50, reconciler.total_pending)
            reconciler.do_unmark('1 sdjfkljsdfkljsdl 2')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-30, reconciler.total_pending)
            reconciler.default('1')
            self.verify_equal_floats(-15, reconciler.total_cleared)
            self.verify_equal_floats(-50, reconciler.total_pending)


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


class StatementTests(MockRawInput, Redirector):
    pass
